"""OpenAI client wrapper + JSON extraction from model text."""

import json
import os
import re
from typing import Any

from openai import OpenAI

from constants import MODEL

_studio: OpenAI | None = None


def openai_client() -> OpenAI:
    global _studio
    if _studio is None:
        k = os.getenv("OPENAI_API_KEY") or os.getenv("OPEN_AI_API_KEY")
        if not k:
            raise RuntimeError(
                "Set OPENAI_API_KEY (or OPEN_AI_API_KEY) in the environment or .env — "
                "see README; don't commit keys."
            )
        _studio = OpenAI(api_key=k)
    return _studio


def chat(messages: list[dict[str, str]], max_tokens=2000, temperature=0.7) -> str:
    r = openai_client().chat.completions.create(
        model=MODEL,
        messages=messages,
        max_tokens=max_tokens,
        temperature=temperature,
    )
    chunk = r.choices[0].message.content
    return chunk or ""


def grab_json_dict(raw: str) -> dict[str, Any]:
    raw = raw.strip()
    m = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", raw, re.I)
    if m:
        raw = m.group(1).strip()
    i, j = raw.find("{"), raw.rfind("}")
    if i < 0 or j <= i:
        raise ValueError("no json object in model output")
    return json.loads(raw[i : j + 1])
