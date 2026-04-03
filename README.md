# Chami-s_Bot

🤖 Chami's Bot
This is a fun LLM project built using Google Gemini models and Streamlit, designed as an interactive demo showcasing both conversational AI and multimodal capabilities.

![Demo Screenshot](image_bot.PNG)

✨ Features

💬 Chat Interface
- Interactive chatbot UI using Streamlit
- Maintains short conversation history
- Clean Markdown-formatted responses

⚡ Quick Actions
- Summarize responses
- Explain step-by-step
- Rewrite shorter

🖼️ Image Analysis (Multimodal)
- Upload an image and:
- Describe the image
- Analyze content
- Extract text (OCR)
- Combine image + text queries

📊 Logging
- Real-time logs panel
 
 Tracks:
- User inputs
- Model usage
- Errors

⚙️ Custom Controls
- Model selection
- Temperature tuning
- Output token control
- Editable system prompt

💾 Persistence
- Save conversation locally
- Export chat as .txt

🧱 Tech Stack
- Frontend: Streamlit
- LLM: Google Gemini (google-genai)
- Environment: Python 3.9+
- Libraries: Pillow, python-dotenv


📦 Installation
```bash
git clone <your-repo-url>
cd Chami-s_Bot
pip install -r requirements.txt
```

🔑 Setup

Create a .env file in the root directory:

```bash
GEMINI_API_KEY=your_api_key_here
GEMINI_MODEL=gemini-2.5-flash
```


▶️ Run the App
```bash
streamlit run streamlit_app.py
```

Open in browser:
```bash
http://localhost:8501
```

📁 Project Structure

Chami-s_Bot/
│
├── streamlit_app.py
├── .env
├── requirements.txt
├── chat_data/
│   └── conversation.json
├── demo.png
└── README.md


👤 Author

Chamani Shiranthika

Simon Fraser University



⭐ If Useful

If you found this helpful, consider giving the repo a ⭐