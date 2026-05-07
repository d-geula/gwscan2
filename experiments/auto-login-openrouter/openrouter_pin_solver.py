import base64
import json
import os
import random
import time
from collections.abc import Callable
from typing import Any

import httpx


OPENROUTER_CHAT_COMPLETIONS_URL = "https://openrouter.ai/api/v1/chat/completions"
RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}
DEFAULT_RETRY_DEADLINE_SECONDS = 5 * 60
INITIAL_RETRY_DELAY_SECONDS = 5.0
MAX_RETRY_DELAY_SECONDS = 60.0
MAX_OUTPUT_TOKENS = 2048

PIN_PROMPT = (
    "A vision/reasoning test for you: in this image there are 3 numbers; "
    "they can be any combination of numbers from 1 to 9; they can be written "
    '(e.g. "one") or represented as dots you have to count. The final answer '
    "should be an array of three integers corresponding to the three numbers "
    "represented in the image. Try to get it right as best you can."
)

PIN_RESPONSE_FORMAT = {
    "type": "json_schema",
    "json_schema": {
        "name": "pin_solution",
        "strict": True,
        "schema": {
            "type": "object",
            "required": ["numbers"],
            "additionalProperties": False,
            "properties": {
                "numbers": {
                    "type": "array",
                    "items": {"type": "integer"},
                    "minItems": 3,
                    "maxItems": 3,
                },
            },
        },
    },
}

OPENROUTER_PROVIDER_ROUTING = {
    "order": ["google-vertex", "google-ai-studio"],
    "allow_fallbacks": True,
    "require_parameters": True,
}

OPENROUTER_REASONING = {
    "effort": "low",
    "exclude": True,
}


class OpenRouterPinSolverError(RuntimeError):
    pass


def _retry_delay(attempt: int) -> float:
    backoff = min(
        INITIAL_RETRY_DELAY_SECONDS * (2 ** (attempt - 1)),
        MAX_RETRY_DELAY_SECONDS,
    )
    return random.uniform(0.5 * backoff, backoff)


def _format_http_error(exc: httpx.HTTPStatusError) -> str:
    try:
        payload = exc.response.json()
    except json.JSONDecodeError:
        payload = exc.response.text
    return f"{exc.response.status_code}: {payload!r}"


def _is_retryable_openrouter_error(exc: Exception) -> bool:
    if isinstance(exc, httpx.TimeoutException | httpx.TransportError):
        return True
    if isinstance(exc, httpx.HTTPStatusError):
        return exc.response.status_code in RETRYABLE_STATUS_CODES
    return False


def _post_chat_completion_with_retries(
    *,
    api_key: str,
    payload: dict[str, Any],
    logger: Callable[[str], None],
    deadline_seconds: float = DEFAULT_RETRY_DEADLINE_SECONDS,
) -> dict[str, Any]:
    started_at = time.monotonic()
    attempt = 1

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    while True:
        try:
            if attempt > 1:
                logger(f"Retrying OpenRouter PIN decode (attempt {attempt})")

            with httpx.Client(timeout=120) as client:
                response = client.post(
                    OPENROUTER_CHAT_COMPLETIONS_URL,
                    headers=headers,
                    json=payload,
                )
                response.raise_for_status()
                return response.json()
        except (httpx.HTTPError, json.JSONDecodeError) as exc:
            elapsed = time.monotonic() - started_at
            if not _is_retryable_openrouter_error(exc):
                detail = (
                    _format_http_error(exc)
                    if isinstance(exc, httpx.HTTPStatusError)
                    else str(exc)
                )
                raise OpenRouterPinSolverError(
                    f"OpenRouter PIN decode failed: {detail}"
                ) from None

            if elapsed >= deadline_seconds:
                detail = (
                    _format_http_error(exc)
                    if isinstance(exc, httpx.HTTPStatusError)
                    else str(exc)
                )
                raise OpenRouterPinSolverError(
                    "OpenRouter PIN decode failed after"
                    f" {attempt} attempts over {elapsed:.0f}s: {detail}"
                ) from None

            delay = min(_retry_delay(attempt), deadline_seconds - elapsed)
            detail = (
                _format_http_error(exc)
                if isinstance(exc, httpx.HTTPStatusError)
                else str(exc)
            )
            logger(
                "OpenRouter PIN decode hit retryable"
                f" {detail}; waiting {delay:.1f}s before retry"
            )
            time.sleep(delay)
            attempt += 1


def _extract_response_text(response_payload: dict[str, Any]) -> str:
    choices = response_payload.get("choices")
    if not isinstance(choices, list) or not choices:
        raise RuntimeError(f"Unexpected OpenRouter payload: {response_payload!r}")

    message = choices[0].get("message")
    if not isinstance(message, dict):
        raise RuntimeError(f"Unexpected OpenRouter message: {response_payload!r}")

    content = message.get("content")
    if isinstance(content, str):
        return content

    if isinstance(content, list):
        text_parts = [
            part.get("text", "")
            for part in content
            if isinstance(part, dict) and part.get("type") == "text"
        ]
        return "".join(text_parts)

    raise RuntimeError(f"Unexpected OpenRouter content: {response_payload!r}")


def solve_pin_image(
    image_bytes: bytes, model: str, logger: Callable[[str], None] | None = None
) -> str:
    if logger is None:
        logger = lambda _: None

    api_key = os.getenv("OPENROUTER_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("Missing required API key in .env: OPENROUTER_API_KEY")

    image_b64 = base64.b64encode(image_bytes).decode("ascii")
    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": PIN_PROMPT},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{image_b64}",
                        },
                    },
                ],
            }
        ],
        "max_tokens": MAX_OUTPUT_TOKENS,
        "reasoning": OPENROUTER_REASONING,
        "response_format": PIN_RESPONSE_FORMAT,
        "provider": OPENROUTER_PROVIDER_ROUTING,
    }
    response_payload = _post_chat_completion_with_retries(
        api_key=api_key,
        payload=payload,
        logger=logger,
    )

    response_text = _extract_response_text(response_payload)
    if not response_text:
        raise RuntimeError("OpenRouter returned an empty response for the captcha")

    payload = json.loads(response_text)

    numbers = payload.get("numbers")
    if not isinstance(numbers, list) or len(numbers) != 3:
        raise RuntimeError(f"Unexpected OpenRouter payload: {payload!r}")

    if any(
        not isinstance(number, int) or number < 0 or number > 9 for number in numbers
    ):
        raise RuntimeError(f"Unexpected number values from OpenRouter: {numbers!r}")

    return "".join(str(number) for number in numbers)
