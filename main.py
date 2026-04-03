"""Interactive CLI chatbot for Gemini via the Google GenAI SDK.

This version is more defensive than the original:
- supports one-shot and interactive chat modes
- lets you override the model from the command line
- catches quota/rate-limit errors and falls back to a cheaper model by default
- prints user-friendly errors instead of dumping raw stack traces
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import replace
from typing import Iterable, Optional

from gemini_service import GeminiService
from settings import Settings, get_settings

DEFAULT_FALLBACK_MODELS = ("gemini-2.5-flash", "gemini-2.5-flash-lite")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Chat with Gemini from Python 3.9+ using the Google GenAI SDK."
    )
    parser.add_argument(
        "--oneshot",
        action="store_true",
        help="Send one prompt and exit instead of starting an interactive chat.",
    )
    parser.add_argument(
        "prompt",
        nargs="*",
        help="Prompt text for --oneshot mode.",
    )
    parser.add_argument(
        "--model",
        default=None,
        help="Override GEMINI_MODEL for this run (for example: gemini-2.5-flash).",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=None,
        help="Override GEMINI_TEMPERATURE for this run.",
    )
    parser.add_argument(
        "--max-output-tokens",
        type=int,
        default=None,
        help="Override GEMINI_MAX_OUTPUT_TOKENS for this run.",
    )
    parser.add_argument(
        "--no-fallback",
        action="store_true",
        help="Disable automatic fallback to cheaper models when quota errors happen.",
    )
    return parser


def _quota_error_message(exc: Exception) -> bool:
    text = str(exc).lower()
    return "429" in text or "resource_exhausted" in text or "quota" in text


def _build_settings(base: Settings, args: argparse.Namespace, model: Optional[str] = None) -> Settings:
    next_model = model if model is not None else (args.model or base.model)
    next_temperature = base.temperature if args.temperature is None else args.temperature
    next_max_tokens = base.max_output_tokens if args.max_output_tokens is None else args.max_output_tokens
    return replace(
        base,
        model=next_model,
        temperature=next_temperature,
        max_output_tokens=next_max_tokens,
    )


def _service_with_settings(settings: Settings) -> GeminiService:
    return GeminiService(settings)


def _try_models(models: Iterable[str], base: Settings, args: argparse.Namespace, prompt: str, oneshot: bool) -> str:
    last_exc: Optional[Exception] = None
    for model in models:
        settings = _build_settings(base, args, model=model)
        service = _service_with_settings(settings)
        try:
            return service.one_shot(prompt) if oneshot else service.reply(prompt)
        except Exception as exc:
            last_exc = exc
            if not _quota_error_message(exc):
                raise
    assert last_exc is not None
    raise last_exc


def run_interactive(base: Settings, args: argparse.Namespace) -> None:
    print(f"Gemini chat ready. Model: {args.model or base.model}")
    print("Type 'exit' or 'quit' to stop. Press Ctrl+C to leave.\n")

    current_model = args.model or base.model
    service = _service_with_settings(_build_settings(base, args, model=current_model))

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye.")
            return

        if not user_input:
            continue
        if user_input.lower() in {"exit", "quit"}:
            print("Bye.")
            return

        try:
            answer = service.reply(user_input)
            print(f"Gemini: {answer}\n")
            continue
        except Exception as exc:
            if _quota_error_message(exc) and not args.no_fallback:
                fallback_models = [m for m in DEFAULT_FALLBACK_MODELS if m != current_model]
                try:
                    answer = _try_models(fallback_models, base, args, user_input, oneshot=False)
                    current_model = fallback_models[0]
                    service = _service_with_settings(_build_settings(base, args, model=current_model))
                    print(f"Chami's bot: {answer}\n")
                    continue
                except Exception as fallback_exc:
                    print(
                        "Error: quota/rate-limit error on the selected model, and fallback also failed.\n"
                        f"Details: {fallback_exc}\n",
                        file=sys.stderr,
                    )
                    continue

            print(f"Error: {exc}\n", file=sys.stderr)


def run_oneshot(base: Settings, args: argparse.Namespace, prompt: str) -> None:
    models_to_try = [args.model or base.model]
    if not args.no_fallback:
        for fallback in DEFAULT_FALLBACK_MODELS:
            if fallback not in models_to_try:
                models_to_try.append(fallback)

    try:
        answer = _try_models(models_to_try, base, args, prompt, oneshot=True)
        print(answer)
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    base_settings = get_settings()

    if args.oneshot:
        prompt = " ".join(args.prompt).strip()
        if not prompt:
            parser.error("--oneshot requires a prompt.")
        run_oneshot(base_settings, args, prompt)
        return

    run_interactive(base_settings, args)


if __name__ == "__main__":
    main()