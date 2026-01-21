from __future__ import annotations

import os
from typing import Optional

from openai import OpenAI


DEFAULT_BASE_URL = "https://router.huggingface.co/v1"
DEFAULT_MODEL = "meta-llama/Llama-3.2-1B-Instruct:novita"


def summarize(text: str) -> Optional[str]:
    token = os.getenv("HF_TOKEN")
    if not token or not text:
        return None

    client = OpenAI(
        base_url=os.getenv("HF_BASE_URL", DEFAULT_BASE_URL),
        api_key=token,
        timeout=20.0,
        max_retries=0,
    )
    try:
        completion = client.chat.completions.create(
            model=os.getenv("HF_MODEL", DEFAULT_MODEL),
            messages=[{"role": "user", "content": text}],
            temperature=0.2,
            max_tokens=120,
            timeout=20,
        )
    except Exception as exc:
        if os.getenv("HF_DEBUG") == "1":
            print(f"HF summarize error: {exc}")
        return None

    if not completion.choices:
        return None
    return completion.choices[0].message.content
