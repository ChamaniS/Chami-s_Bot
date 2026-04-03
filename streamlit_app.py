import os
import certifi

# Force Python to use a valid CA bundle.
os.environ["SSL_CERT_FILE"] = certifi.where()

# Clear common env vars that can point to broken cert paths.
os.environ.pop("REQUESTS_CA_BUNDLE", None)
os.environ.pop("CURL_CA_BUNDLE", None)

from google import genai
from google.genai import types
import streamlit as st
from dotenv import load_dotenv
from datetime import datetime
import traceback

# =========================================================
# LOAD ENV FILE  (CRITICAL FIX)
# =========================================================
load_dotenv()

# =========================================================
# PAGE CONFIG
# =========================================================
st.set_page_config(page_title="Chami's Bot", page_icon="🤖", layout="wide")

# =========================================================
# STATE INIT
# =========================================================
if "messages" not in st.session_state:
    st.session_state.messages = []

if "logs" not in st.session_state:
    st.session_state.logs = []

# =========================================================
# CONFIG FROM ENV
# =========================================================
API_KEY = os.getenv("GEMINI_API_KEY")
DEFAULT_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

# =========================================================
# LOGGING
# =========================================================
def log(msg, level="INFO"):
    timestamp = datetime.now().strftime("%H:%M:%S")
    line = f"{timestamp} | {level} | {msg}"
    st.session_state.logs.append(line)
    st.session_state.logs = st.session_state.logs[-200:]
    print(line)


# =========================================================
# GEMINI CALL
# =========================================================
def ask_gemini(prompt, model):
    client = genai.Client(api_key=API_KEY)

    full_prompt = f"""
You are a helpful assistant.
Give a detailed answer.
Use clear headings and bullet points when appropriate.
Do not answer in only one sentence.

User question:
{prompt}
"""

    config = types.GenerateContentConfig(
        temperature=0.7,
        max_output_tokens=1500,
    )

    response = client.models.generate_content(
        model=model,
        contents=full_prompt,
        config=config,
    )

    return getattr(response, "text", str(response))


# =========================================================
# FALLBACK HANDLER
# =========================================================
def generate_with_fallback(prompt, model):
    models = [model, "gemini-2.5-flash", "gemini-2.5-flash-lite"]

    for m in models:
        try:
            log(f"Trying model: {m}")
            reply = ask_gemini(prompt, m)
            return reply, m
        except Exception as e:
            err = str(e).lower()
            log(f"{m} failed: {e}", "ERROR")

            if not any(k in err for k in ["429", "quota", "resource_exhausted"]):
                raise

    raise RuntimeError("All models failed")


# =========================================================
# SIDEBAR
# =========================================================
st.sidebar.title("Settings")

st.sidebar.write("API key loaded:", "✅ Yes" if API_KEY else "❌ No")

model = st.sidebar.text_input("Model", DEFAULT_MODEL)

if st.sidebar.button("Clear Chat"):
    st.session_state.messages = []
    st.rerun()

if st.sidebar.button("Clear Logs"):
    st.session_state.logs = []
    st.rerun()

# =========================================================
# MAIN UI
# =========================================================
st.title("Chami's Bot")
st.caption("Simple browser UI with logs")

col1, col2 = st.columns([2, 1])

# ---------------- CHAT ----------------
with col1:
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    prompt = st.chat_input("Type your message...")

    if prompt:
        if not API_KEY:
            st.error("GEMINI_API_KEY is missing. Check your .env file.")
            st.stop()

        st.session_state.messages.append({"role": "user", "content": prompt})
        log(f"User: {prompt}")

        try:
            with st.spinner("Thinking..."):
                reply, used_model = generate_with_fallback(prompt, model)

            st.session_state.messages.append(
                {"role": "assistant", "content": reply}
            )
            log(f"Reply generated using {used_model}")

        except Exception as e:
            error_msg = f"Error: {e}"
            log(error_msg, "ERROR")

            st.session_state.messages.append(
                {"role": "assistant", "content": error_msg}
            )

            # full traceback in UI
            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": "```text\n"
                    + traceback.format_exc()
                    + "\n```",
                }
            )

        st.rerun()

# ---------------- LOG PANEL ----------------
with col2:
    st.subheader("Logs")
    logs = "\n".join(st.session_state.logs) or "No logs yet"
    st.text_area("Log output", logs, height=500)

    st.subheader("Status")
    st.write(f"Messages: {len(st.session_state.messages)}")