import os
from google import genai

print("API key set:", bool(os.getenv("GEMINI_API_KEY")))
print("GAC:", os.getenv("GOOGLE_APPLICATION_CREDENTIALS"))
print("VERTEX:", os.getenv("GOOGLE_GENAI_USE_VERTEXAI"))

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
resp = client.models.generate_content(
    model="gemini-2.5-flash",
    contents="Say hello in one short sentence."
)
print(resp.text)