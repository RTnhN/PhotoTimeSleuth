import base64
import re
from typing import Optional

import openai


def ask_ai_for_date(image_path: str, api_key: str) -> Optional[str]:
    """Send the given image to OpenAI to estimate a date.

    Parameters
    ----------
    image_path: str
        Path to the image file.
    api_key: str
        OpenAI API key.

    Returns
    -------
    Optional[str]
        A date string in ``YYYY-MM-DD`` format if one can be parsed from the
        response, otherwise ``None``.
    """

    client = openai.OpenAI(api_key=api_key)

    with open(image_path, "rb") as img_file:
        encoded = base64.b64encode(img_file.read()).decode("utf-8")

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": (
                            "Estimate the date this photo was taken. "
                            "Respond only with a date in YYYY-MM-DD format."
                        ),
                    },
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{encoded}"},
                    },
                ],
            }
        ],
        max_tokens=20,
    )

    message = response.choices[0].message.content.strip()
    match = re.search(r"\d{4}[-:]\d{2}[-:]\d{2}", message)
    if match:
        return match.group(0).replace(":", "-")
    return None
