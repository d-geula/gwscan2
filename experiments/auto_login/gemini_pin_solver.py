import json
import os
from collections.abc import Callable

from google import genai
from google.genai import types


PIN_PROMPT = (
    "A vision/reasoning test for you: in this image there are 3 numbers; "
    "they can be any combination of numbers from 1 to 9; they can be written "
    '(e.g. "one") or represented as dots you have to count. The final answer '
    "should be an array of three integers corresponding to the three numbers "
    "represented in the image. Try to get it right as best you can."
)


def solve_pin_image(
    image_bytes: bytes, model: str, logger: Callable[[str], None] | None = None
) -> str:
    if logger is None:
        logger = lambda _: None

    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("Missing required API key in .env: GEMINI_API_KEY")

    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model=model,
        contents=[
            types.Content(
                role="user",
                parts=[
                    types.Part.from_bytes(mime_type="image/png", data=image_bytes),
                    types.Part.from_text(text=PIN_PROMPT),
                ],
            )
        ],
        config=types.GenerateContentConfig(
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
        ),
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
