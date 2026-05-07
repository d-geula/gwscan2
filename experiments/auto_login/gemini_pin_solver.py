import json
import os
import random
import time
from collections.abc import Callable

from google import genai
from google.genai import errors
from google.genai import types


RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}
DEFAULT_RETRY_DEADLINE_SECONDS = 10 * 60
INITIAL_RETRY_DELAY_SECONDS = 5.0
MAX_RETRY_DELAY_SECONDS = 60.0

PIN_PROMPT = (
    "A vision/reasoning test for you: in this image there are 3 numbers; "
    "they can be any combination of numbers from 1 to 9; they can be written "
    '(e.g. "one") or represented as dots you have to count. The final answer '
    "should be an array of three integers corresponding to the three numbers "
    "represented in the image. Try to get it right as best you can."
)


class GeminiPinSolverError(RuntimeError):
    pass


def _format_gemini_error(exc: errors.APIError) -> str:
    status = exc.status or exc.__class__.__name__
    message = exc.message or str(exc)
    return f"{exc.code} {status}: {message}"


def _is_retryable_gemini_error(exc: Exception) -> bool:
    if isinstance(exc, errors.ServerError):
        return True
    if isinstance(exc, errors.APIError):
        return exc.code in RETRYABLE_STATUS_CODES
    return False


def _retry_delay(attempt: int) -> float:
    backoff = min(
        INITIAL_RETRY_DELAY_SECONDS * (2 ** (attempt - 1)),
        MAX_RETRY_DELAY_SECONDS,
    )
    return random.uniform(0.5 * backoff, backoff)


def _generate_content_with_retries(
    client: genai.Client,
    *,
    model: str,
    contents: list[types.Content],
    config: types.GenerateContentConfig,
    logger: Callable[[str], None],
    deadline_seconds: float = DEFAULT_RETRY_DEADLINE_SECONDS,
) -> types.GenerateContentResponse:
    started_at = time.monotonic()
    attempt = 1

    while True:
        try:
            if attempt > 1:
                logger(f"Retrying Gemini PIN decode (attempt {attempt})")
            return client.models.generate_content(
                model=model,
                contents=contents,
                config=config,
            )
        except errors.APIError as exc:
            elapsed = time.monotonic() - started_at
            if not _is_retryable_gemini_error(exc):
                raise GeminiPinSolverError(
                    f"Gemini PIN decode failed: {_format_gemini_error(exc)}"
                ) from None

            if elapsed >= deadline_seconds:
                raise GeminiPinSolverError(
                    "Gemini PIN decode failed after"
                    f" {attempt} attempts over {elapsed:.0f}s:"
                    f" {_format_gemini_error(exc)}"
                ) from None

            delay = min(_retry_delay(attempt), deadline_seconds - elapsed)
            logger(
                "Gemini PIN decode hit retryable"
                f" {_format_gemini_error(exc)};"
                f" waiting {delay:.1f}s before retry"
            )
            time.sleep(delay)
            attempt += 1


def solve_pin_image(
    image_bytes: bytes, model: str, logger: Callable[[str], None] | None = None
) -> str:
    if logger is None:
        logger = lambda _: None

    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("Missing required API key in .env: GEMINI_API_KEY")

    client = genai.Client(api_key=api_key)
    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_bytes(mime_type="image/png", data=image_bytes),
                types.Part.from_text(text=PIN_PROMPT),
            ],
        )
    ]
    config = types.GenerateContentConfig(
        max_output_tokens=4000,
        thinking_config=types.ThinkingConfig(thinking_level="LOW"),
        media_resolution="MEDIA_RESOLUTION_HIGH",
        response_mime_type="application/json",
        response_schema=genai.types.Schema(
            type=genai.types.Type.OBJECT,
            required=["numbers"],
            properties={
                "numbers": genai.types.Schema(
                    type=genai.types.Type.ARRAY,
                    items=genai.types.Schema(type=genai.types.Type.INTEGER),
                )
            },
        ),
    )
    response = _generate_content_with_retries(
        client,
        model=model,
        contents=contents,
        config=config,
        logger=logger,
    )

    if not response.text:
        raise RuntimeError("Gemini returned an empty response for the captcha")

    payload = json.loads(response.text)

    numbers = payload.get("numbers")
    if not isinstance(numbers, list) or len(numbers) != 3:
        raise RuntimeError(f"Unexpected Gemini payload: {payload!r}")

    if any(
        not isinstance(number, int) or number < 0 or number > 9 for number in numbers
    ):
        raise RuntimeError(f"Unexpected number values from Gemini: {numbers!r}")

    return "".join(str(number) for number in numbers)
