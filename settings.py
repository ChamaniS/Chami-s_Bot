"""Application settings and environment loading."""

from __future__ import annotations

import os
from dataclasses import dataclass
from dotenv import load_dotenv


load_dotenv()


@dataclass(frozen=True)
class Settings:
    api_key: str
    model: str = "gemini-2.5-pro"
    temperature: float = 0.7
    max_output_tokens: int = 1024
    system_instruction: str = (
        "You are a helpful, direct assistant. Keep answers clear, concise, and correct."
    )


def get_settings() -> Settings:
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY is missing. Put it in a .env file or export it in your shell."
        )

    model = os.getenv("GEMINI_MODEL", "gemini-2.5-pro").strip() or "gemini-2.5-pro"
    temperature_raw = os.getenv("GEMINI_TEMPERATURE", "0.7").strip()
    max_tokens_raw = os.getenv("GEMINI_MAX_OUTPUT_TOKENS", "1024").strip()

    try:
        temperature = float(temperature_raw)
    except ValueError as exc:
        raise RuntimeError("GEMINI_TEMPERATURE must be a number.") from exc

    try:
        max_output_tokens = int(max_tokens_raw)
    except ValueError as exc:
        raise RuntimeError("GEMINI_MAX_OUTPUT_TOKENS must be an integer.") from exc

    return Settings(
        api_key=api_key,
        model=model,
        temperature=temperature,
        max_output_tokens=max_output_tokens,
    )
