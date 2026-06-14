# Mars AI Assistant

A clean Streamlit chatbot project with two separate interfaces:
- `bot.py` for Groq integration
- `chat.py` for Google Gemini integration

![Screenshot](ss.png)

---

## Features

- Conversational chatbot interface with message history
- Voice recording support in `bot.py`
- File upload support in `bot.py` (TXT, CSV, XLSX, PDF, DOCX, PPTX)
- Model selection and temperature control
- Dark-themed UI styling
- API keys managed through `.env`

---

## Quick Start

### 1. Open the project folder

```bash
cd "c:\Users\maiss\Downloads\Chat-bot-master-updated\Chat-bot-master"
```

### 2. Create a virtual environment

```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure API keys

Copy the example file:

```bash
copy .env.example .env
```

Open `.env` and add your keys:

```env
GROQ_API_KEY=your_groq_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here
```

---

## Run the App

### Run the Groq chatbot

```bash
streamlit run bot.py
```

### Run the Gemini chatbot

```bash
streamlit run chat.py
```

Open the app at `http://localhost:8501`.

---

## Project Structure

```
Chat-bot-master/
├── bot.py              # Groq chatbot with voice and file upload support
├── chat.py             # Gemini chatbot interface
├── requirements.txt    # Python dependencies
├── .env.example        # Environment variable template
├── ai.png              # Sidebar logo image
├── ss.png              # Screenshot / icon
└── e.gif               # Animated background image
```

---

## Configuration

### API Keys

- `GROQ_API_KEY` is used by `bot.py`
- `GEMINI_API_KEY` is used by `chat.py`

### Prompt Customization

- `bot.py` includes `SYSTEM_PROMPT` to control the assistant behavior.
- `chat.py` includes the prompt settings for Gemini.

---

## Available Models

### `bot.py` (Groq)

- `llama-3.3-70b-versatile` — recommended
- `llama-3.1-8b-instant` — fast responses
- `gemma2-9b-it` — good for technical tasks
- `mistral-saba-24b` — strong language model

### `chat.py` (Gemini)

- `gemini-2.0-flash` — recommended
- `gemini-1.5-flash`
- `gemini-1.5-pro`

---

## Troubleshooting

- `GROQ_API_KEY missing`: check your `.env` file
- `Groq API key missing`: ensure the key is defined correctly
- Missing `ffmpeg`: install `ffmpeg` if using voice transcription
- `ModuleNotFoundError`: run `pip install -r requirements.txt`

---

## Security

- Do not commit your `.env` file.
- Add `.env` to `.gitignore` if needed.

---

## License

MIT License.

---

*Mars AI Assistant — Streamlit chatbot demo.*
