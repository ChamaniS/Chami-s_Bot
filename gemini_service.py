"""Thin wrapper around the Google GenAI SDK."""

from __future__ import annotations

from google import genai
from google.genai import types

from settings import Settings


class GeminiService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.client = genai.Client(api_key=settings.api_key)
        self.chat = self.client.chats.create(model=settings.model)

    def reply(self, message: str) -> str:
        response = self.chat.send_message(message=message)
        return getattr(response, "text", None) or str(response)

    def one_shot(self, prompt: str) -> str:
        response = self.client.models.generate_content(
            model=self.settings.model,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=self.settings.temperature,
                max_output_tokens=self.settings.max_output_tokens,
            ),
        )
        return getattr(response, "text", None) or str(response)
