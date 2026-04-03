import os
import certifi

# Force Python to use a valid certificate bundle
os.environ["SSL_CERT_FILE"] = certifi.where()
os.environ.pop("REQUESTS_CA_BUNDLE", None)
os.environ.pop("CURL_CA_BUNDLE", None)

import json
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from PIL import Image
import streamlit as st
from google import genai
from google.genai import types

# ----------------------------
# Setup
# ----------------------------
load_dotenv()

APP_DIR = Path(__file__).resolve().parent
DATA_DIR = APP_DIR / "chat_data"
DATA_DIR.mkdir(exist_ok=True)

CHAT_SAVE_PATH = DATA_DIR / "conversation.json"

st.set_page_config(
    page_title="Chami's Bot",
    page_icon="🤖",
    layout="wide",
)

API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
DEFAULT_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

DEFAULT_SYSTEM_PROMPT = """
You are a helpful assistant.
Answer clearly and naturally.
Use short paragraphs and bullet points when helpful.
If the user asks for steps, give step-by-step instructions.
Do not answer in one tiny sentence unless the question is tiny.
""".strip()


# ----------------------------
# State
# ----------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

if "logs" not in st.session_state:
    st.session_state.logs = []

if "model" not in st.session_state:
    st.session_state.model = DEFAULT_MODEL

if "temperature" not in st.session_state:
    st.session_state.temperature = 0.7

if "max_output_tokens" not in st.session_state:
    st.session_state.max_output_tokens = 1200

if "system_prompt" not in st.session_state:
    st.session_state.system_prompt = DEFAULT_SYSTEM_PROMPT


# ----------------------------
# Helpers
# ----------------------------
def log(message: str, level: str = "INFO") -> None:
    timestamp = datetime.now().strftime("%H:%M:%S")
    line = f"{timestamp} | {level} | {message}"
    st.session_state.logs.append(line)
    st.session_state.logs = st.session_state.logs[-200:]
    print(line)


def save_chat() -> None:
    payload = {
        "saved_at": datetime.now().isoformat(timespec="seconds"),
        "model": st.session_state.model,
        "messages": st.session_state.messages,
    }
    CHAT_SAVE_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def export_chat_text() -> str:
    lines = []
    for msg in st.session_state.messages:
        role = msg["role"].capitalize()
        content = msg["content"]
        lines.append(f"{role}: {content}")
        lines.append("")
    return "\n".join(lines).strip()


def build_prompt(user_prompt: str) -> str:
    history = st.session_state.messages[-8:]

    convo_lines = [st.session_state.system_prompt, ""]
    for msg in history:
        role = "User" if msg["role"] == "user" else "Assistant"
        convo_lines.append(f"{role}: {msg['content']}")

    convo_lines.append(f"User: {user_prompt}")
    convo_lines.append("Assistant:")

    return "\n".join(convo_lines)


def get_pil_image(uploaded_file):
    if uploaded_file is None:
        return None
    try:
        return Image.open(uploaded_file).convert("RGB")
    except Exception as e:
        log(f"Failed to open image: {e}", "ERROR")
        return None


def ask_gemini(prompt: str, image=None) -> str:
    if not API_KEY:
        raise RuntimeError("GEMINI_API_KEY is missing. Put it in your .env file.")

    client = genai.Client(api_key=API_KEY)

    config = types.GenerateContentConfig(
        temperature=st.session_state.temperature,
        max_output_tokens=int(st.session_state.max_output_tokens),
    )

    if image is None:
        response = client.models.generate_content(
            model=st.session_state.model,
            contents=prompt,
            config=config,
        )
    else:
        # Multimodal request: text + image
        response = client.models.generate_content(
            model=st.session_state.model,
            contents=[prompt, image],
            config=config,
        )

    text = getattr(response, "text", None)
    return text if text else str(response)


def ask_gemini_with_fallback(user_prompt: str, image=None) -> tuple[str, str]:
    candidates = [
        st.session_state.model,
        "gemini-2.5-flash",
        "gemini-2.5-flash-lite",
    ]

    seen = []
    for model in candidates:
        if model in seen:
            continue
        seen.append(model)

        try:
            st.session_state.model = model
            prompt = build_prompt(user_prompt)
            log(f"Trying model: {model}")
            reply = ask_gemini(prompt, image=image)
            return reply, model
        except Exception as e:
            err = str(e).lower()
            log(f"Model failed: {model} -> {e}", "ERROR")

            quota_like = any(
                key in err for key in ["429", "quota", "resource_exhausted", "rate limit"]
            )

            if not quota_like:
                raise

    raise RuntimeError("All model attempts failed.")


def run_user_turn(text: str, image=None, show_image: bool = True) -> None:
    st.session_state.messages.append({"role": "user", "content": text})
    log(f"User: {text}")

    if image is not None and show_image:
        st.session_state.messages.append(
            {"role": "user", "content": "[Image uploaded for analysis]"}
        )

    try:
        with st.spinner("Thinking..."):
            reply, used_model = ask_gemini_with_fallback(text, image=image)

        st.session_state.messages.append({"role": "assistant", "content": reply})
        log(f"Reply generated using {used_model}")
        save_chat()

    except Exception as e:
        error_text = f"Error: {e}"
        st.session_state.messages.append({"role": "assistant", "content": error_text})
        log(error_text, "ERROR")
        save_chat()


def quick_image_prompt(image, instruction: str) -> None:
    if image is None:
        st.warning("Upload an image first.")
        return
    run_user_turn(instruction, image=image, show_image=True)
    st.rerun()


# ----------------------------
# Sidebar
# ----------------------------
st.sidebar.title("Settings")
st.sidebar.write("API key loaded:", "✅ Yes" if API_KEY else "❌ No")
st.sidebar.write("Working folder:", str(APP_DIR))

st.session_state.model = st.sidebar.text_input(
    "Model",
    value=st.session_state.model,
    help="Try gemini-2.5-flash first. It is more reliable for demos.",
)

st.session_state.temperature = st.sidebar.slider(
    "Temperature",
    min_value=0.0,
    max_value=2.0,
    value=float(st.session_state.temperature),
    step=0.1,
)

st.session_state.max_output_tokens = st.sidebar.slider(
    "Max output tokens",
    min_value=128,
    max_value=4096,
    value=int(st.session_state.max_output_tokens),
    step=128,
)

st.session_state.system_prompt = st.sidebar.text_area(
    "System prompt",
    value=st.session_state.system_prompt,
    height=180,
)

if st.sidebar.button("Clear chat"):
    st.session_state.messages = []
    save_chat()
    st.rerun()

if st.sidebar.button("Clear logs"):
    st.session_state.logs = []
    st.rerun()

chat_export = export_chat_text()
st.sidebar.download_button(
    "Download chat as text",
    data=chat_export,
    file_name="chat_history.txt",
    mime="text/plain",
)

if CHAT_SAVE_PATH.exists():
    st.sidebar.caption(f"Saved chat file: {CHAT_SAVE_PATH.name}")


# ----------------------------
# Main UI
# ----------------------------
st.title("Chami's Bot")
st.caption("Simple browser demo with chat, logs, quick actions, and image analysis.")

col_chat, col_logs = st.columns([2.2, 1])

with col_chat:
    st.subheader("Quick actions")

    q1, q2, q3 = st.columns(3)
    with q1:
        if st.button("Summarize this"):
            run_user_turn("Summarize this in simple bullet points.")
            st.rerun()
    with q2:
        if st.button("Explain step by step"):
            run_user_turn("Explain this step by step.")
            st.rerun()
    with q3:
        if st.button("Rewrite shorter"):
            run_user_turn("Rewrite the last response in a shorter, clearer way.")
            st.rerun()

    st.divider()

    st.subheader("Image upload")
    uploaded_file = st.file_uploader(
        "Upload an image (png, jpg, jpeg, webp)",
        type=["png", "jpg", "jpeg", "webp"],
        accept_multiple_files=False,
    )

    current_image = get_pil_image(uploaded_file)

    if current_image is not None:
        st.image(current_image, caption="Uploaded image", use_container_width=True)

        b1, b2, b3 = st.columns(3)
        with b1:
            if st.button("Describe image"):
                quick_image_prompt(
                    current_image,
                    "Describe this image in detail. Mention visible objects, scene, colors, text, and overall context.",
                )
        with b2:
            if st.button("Analyze image"):
                quick_image_prompt(
                    current_image,
                    "Analyze this image carefully. Explain what is happening, important details, and any notable patterns or issues.",
                )
        with b3:
            if st.button("Read text (OCR)"):
                quick_image_prompt(
                    current_image,
                    "Extract and transcribe all visible text from this image. If text is unclear, say which parts are uncertain.",
                )

    st.divider()

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    user_input = st.chat_input("Type your message...")

    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})
        log(f"User: {user_input}")

        try:
            with st.spinner("Thinking..."):
                reply, used_model = ask_gemini_with_fallback(user_input, image=current_image)

            st.session_state.messages.append({"role": "assistant", "content": reply})
            log(f"Reply generated using {used_model}")
            save_chat()
            st.rerun()

        except Exception as e:
            error_text = f"Error: {e}"
            st.session_state.messages.append({"role": "assistant", "content": error_text})
            log(error_text, "ERROR")
            save_chat()
            st.rerun()

with col_logs:
    st.subheader("Logs")
    log_output = "\n".join(st.session_state.logs) if st.session_state.logs else "No logs yet."
    st.text_area("Log output", value=log_output, height=420)

    st.subheader("Status")
    st.write(f"Messages: {len(st.session_state.messages)}")
    st.write(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")