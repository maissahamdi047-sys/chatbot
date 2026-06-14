import os
from pathlib import Path
import streamlit as st
import requests
import json
import base64
from datetime import datetime
import time
import pytz
import pandas as pd
from streamlit_mic_recorder import mic_recorder
from io import BytesIO
import speech_recognition as sr
from pydub import AudioSegment
from dotenv import load_dotenv
from pypdf import PdfReader
from docx import Document
from pptx import Presentation

# Base path for local project assets
BASE_DIR = Path(__file__).resolve().parent

# Load environment variables
load_dotenv()

# Configure Streamlit page settings
st.set_page_config(
    page_title="Chat with Mars",
    page_icon="ss.png",
    layout="centered",
    initial_sidebar_state="expanded"
)

# Constants — clé API depuis variable d'environnement
GROQ_API_KEY = os.getenv(
    "GROQ_API_KEY",
    "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"
)
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

# Modèles Groq à jour (juin 2025)
AVAILABLE_MODELS = {
    "Llama 3.3 70B (Recommandé)": "llama-3.3-70b-versatile",
    "Llama 3.1 8B (Rapide)": "llama-3.1-8b-instant",
    "Gemma 2 9B": "gemma2-9b-it",
    "Mistral Saba 24B": "mistral-saba-24b",
}

SYSTEM_PROMPT = """Tu es Mars, un assistant IA avancé, intelligent et bienveillant.
Tu réponds toujours de manière claire, précise et utile.
Si l'utilisateur te pose une question en français, réponds en français.
Si la question est en anglais, réponds en anglais.
Tu es honnête sur tes limites et tu ne fabricques pas d'informations."""


# Function to convert image to base64
def get_base64(image_path):
    full_path = BASE_DIR / image_path
    try:
        with open(full_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode('utf-8')
    except FileNotFoundError:
        return ""


# Apply fullscreen background with enhanced styling
background_image = get_base64("e.gif")

bg_style = (
    f'background-image: url("data:image/gif;base64,{background_image}");'
    if background_image
    else "background-color: #000;"
)

theme_css = """
    /* Fixed dark theme */
    html, body, .stApp, .block-container, .main, .css-1d391kg, .css-18e3th9, .css-1v0mbdj, .css-1n76uvr, .css-1lcbmhc { background: #03040b !important; color: #fff !important; }
    .stApp, .block-container, .main, .css-1d391kg, .css-18e3th9, .css-1y4p8pa, .css-1k2uqdt, .css-1n76uvr { background: rgba(3,4,11,0.98) !important; }
    .stChatMessage { background-color: rgba(255,255,255,0.05) !important; color: #fff !important; border: 1px solid rgba(255,255,255,0.08) !important; box-shadow: 0 2px 10px rgba(0,0,0,0.25) !important; }
    .stChatMessage p, .stText, .css-1dq8tca, .css-1w0ulz5, .stTextInput, .stTextArea, .stMarkdown { color: #fff !important; }
    [data-testid="stChatMessage"] [data-testid="chatAvatarIcon-user"] { background-color: #4a8cff !important; }
    [data-testid="stChatMessage"] [data-testid="chatAvatarIcon-assistant"] { background-color: #ff6b4a !important; }
    .stTextInput > div > div > input, .stTextArea > div > textarea, .stTextArea textarea, .stTextInput input { background-color: rgba(255,255,255,0.08) !important; color: #fff !important; border: 1px solid rgba(255,255,255,0.12) !important; }
    .stButton > button, button.css-1emrehy.edgvbvh3, button.css-1y4xawy, button.css-1v0mbdj { background-color: #4a8cff !important; color: white !important; }
    .css-1d391kg, .css-1lsmgbg, .css-1f0zojk { background: #03040b !important; }
    button[aria-label*="Theme"], button[aria-label*="Thème"], button[title*="Theme"], button[title*="Thème"], button[title*="Mode"], button[aria-label*="Paramètres"], button[title*="Paramètres"] { display: none !important; }
"""

st.markdown(
    f"""
    <style>
    /* Main container */
    .stApp {{
        {bg_style}
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
        background-attachment: fixed;
        display: flex;
        flex-direction: column;
        min-height: 100vh;
    }}

    /* Chat message styling (base) */
    .stChatMessage {{
        border-radius: 15px;
        margin-bottom: 15px;
        padding: 12px 15px;
    }}

    /* Fix chat input at bottom */
    .stContainer:has(> [data-testid="stChatInputContainer"]) {{
        position: fixed !important;
        bottom: 0 !important;
        left: 0 !important;
        right: 0 !important;
        width: 100% !important;
        background: rgba(3, 4, 11, 0.98) !important;
        padding: 15px 20px !important;
        border-top: 1px solid rgba(255, 255, 255, 0.08) !important;
        z-index: 999 !important;
        box-shadow: 0 -2px 15px rgba(0, 0, 0, 0.3) !important;
    }}

    /* Add padding to main content */
    .main {{
        padding-bottom: 120px !important;
    }}

    /* Scrollable chat area */
    .block-container {{
        padding-bottom: 120px !important;
    }}

    {theme_css}
    </style>
    """,
    unsafe_allow_html=True,
)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Bonjour ! Je suis Mars, votre assistant IA. Comment puis-je vous aider ?"}
    ]
if "model" not in st.session_state:
    st.session_state.model = "llama-3.3-70b-versatile"
if "temperature" not in st.session_state:
    st.session_state.temperature = 0.7
if "uploaded_files" not in st.session_state:
    st.session_state.uploaded_files = {}
if "conversation_started" not in st.session_state:
    st.session_state.conversation_started = datetime.now(pytz.utc)
if "audio_bytes" not in st.session_state:
    st.session_state.audio_bytes = None
if "transcription_language" not in st.session_state:
    st.session_state.transcription_language = "fr-FR"


# Function to transcribe audio
def transcribe_audio(audio_bytes, language="fr-FR"):
    try:
        audio_buffer = BytesIO(audio_bytes)
        audio_buffer.seek(0)

        r = sr.Recognizer()
        try:
            with sr.AudioFile(audio_buffer) as source:
                audio_data = r.record(source)
        except Exception:
            audio_buffer.seek(0)
            try:
                audio = AudioSegment.from_file(audio_buffer)
                wav_file = BytesIO()
                audio.export(wav_file, format="wav")
                wav_file.seek(0)
                with sr.AudioFile(wav_file) as source:
                    audio_data = r.record(source)
            except FileNotFoundError as ff_error:
                st.error(
                    "Erreur de transcription : ffmpeg introuvable. "
                    "Installez ffmpeg sur votre système ou enregistrez en WAV."
                )
                return None
            except Exception as inner_error:
                st.error(f"Erreur de transcription : {str(inner_error)}")
                return None

        text = r.recognize_google(audio_data, language=language)
        return text
    except Exception as e:
        st.error(f"Erreur de transcription : {str(e)}")
        return None


# Function to call Groq API
def call_groq_api(messages, model):
    if not GROQ_API_KEY:
        return "⚠️ Clé API Groq manquante. Définissez la variable d'environnement `GROQ_API_KEY`."

    # Inject system prompt
    full_messages = [{"role": "system", "content": SYSTEM_PROMPT}] + messages

    data = {
        "model": model,
        "messages": full_messages,
        "temperature": st.session_state.temperature,
        "max_tokens": 2048,
        "top_p": 0.9,
        "frequency_penalty": 0.1,
        "presence_penalty": 0.1
    }

    try:
        response = requests.post(
            GROQ_API_URL,
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            },
            json=data,
            timeout=30
        )

        if response.status_code == 200:
            response_data = response.json()
            return response_data['choices'][0]['message']['content']
        else:
            error_msg = f"Erreur API : {response.status_code}"
            try:
                error_data = response.json()
                error_msg += f" — {error_data.get('error', {}).get('message', 'Erreur inconnue')}"
            except Exception:
                error_msg += f" — {response.text[:200]}"
            return f"⚠️ {error_msg}"

    except requests.exceptions.Timeout:
        return "⚠️ Délai d'attente dépassé. Veuillez réessayer."
    except Exception as e:
        return f"⚠️ Erreur inattendue : {str(e)}"


# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    ai_image_path = BASE_DIR / "ai.png"
    if ai_image_path.exists():
        st.image(str(ai_image_path), width=150)
    else:
        st.write("## Mars")

    st.title("Paramètres Mars")

    # Model selection
    selected_model_label = st.selectbox(
        "Choisir le modèle IA",
        options=list(AVAILABLE_MODELS.keys()),
        index=0,
        key="model_select"
    )
    st.session_state.model = AVAILABLE_MODELS[selected_model_label]

    # Temperature control
    st.session_state.temperature = st.slider(
        "Niveau de créativité",
        min_value=0.1,
        max_value=1.0,
        value=st.session_state.temperature,
        step=0.1,
        help="Des valeurs élevées rendent les réponses plus créatives mais moins factuelles"
    )

    # Transcription language selector
    language_map = {
        "Français": "fr-FR",
        "English": "en-US",
        "Español": "es-ES",
        "Deutsch": "de-DE",
        "Italiano": "it-IT",
        "Português": "pt-PT",
        "中文": "zh-CN",
        "日本語": "ja-JP",
        "한국어": "ko-KR"
    }
    selected_lang = st.selectbox(
        "Langue de transcription",
        options=list(language_map.keys()),
        index=list(language_map.keys()).index("Français"),
        key="lang_select"
    )
    st.session_state.transcription_language = language_map[selected_lang]

    # File uploader
    uploaded_file = st.file_uploader(
        "Importer un fichier à analyser",
        type=["txt", "pdf", "csv", "xlsx", "docx", "pptx"],
        accept_multiple_files=False
    )

    if uploaded_file:
        st.session_state.uploaded_files[uploaded_file.name] = {
            "file": uploaded_file,
            "details": {
                "filename": uploaded_file.name,
                "filetype": uploaded_file.type,
                "filesize": uploaded_file.size
            }
        }
        st.success(f"Fichier « {uploaded_file.name} » importé !")

    # Conversation stats
    st.divider()
    st.subheader("Statistiques")
    duration = datetime.now(pytz.utc) - st.session_state.conversation_started
    st.write(f"⏱️ Durée : {duration.seconds // 60}m {duration.seconds % 60}s")
    st.write(f"💬 Messages : {len([m for m in st.session_state.messages if m['role'] == 'user'])}")

    if st.button("🗑️ Effacer la conversation"):
        st.session_state.messages = [
            {"role": "assistant", "content": "Conversation effacée. Comment puis-je vous aider ?"}
        ]
        st.rerun()

# ── Main interface ────────────────────────────────────────────────────────────
st.title("🪐 Mars AI Assistant")

# Display uploaded files
if st.session_state.uploaded_files:
    with st.expander("📁 Fichiers importés"):
        for filename, file_data in list(st.session_state.uploaded_files.items()):
            col1, col2 = st.columns([3, 1])
            col1.write(f"**{filename}** ({file_data['details']['filetype']})")
            if col2.button("Supprimer", key=f"remove_{filename}"):
                del st.session_state.uploaded_files[filename]
                st.rerun()

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Voice + text input
with st.container():
    col1, col2 = st.columns([5, 1])

    with col1:
        user_prompt = st.chat_input("Écrire un message à Mars…", key="chat_input")

    with col2:
        audio_bytes = mic_recorder(
            start_prompt="🎙️",
            stop_prompt="⏹️",
            just_once=True,
            use_container_width=True,
            format="wav",
            key="recorder"
        )

        if audio_bytes:
            st.session_state.audio_bytes = audio_bytes['bytes']
            st.toast("Audio enregistré ! Transcription…", icon="🎤")
            transcription = transcribe_audio(st.session_state.audio_bytes, language=st.session_state.transcription_language)
            if transcription:
                st.session_state.transcription = transcription
                st.rerun()

# Handle voice transcription
if "transcription" in st.session_state and st.session_state.transcription:
    user_prompt = st.session_state.transcription
    del st.session_state.transcription

# Handle user input
if user_prompt:
    st.session_state.messages.append({"role": "user", "content": user_prompt})

    with st.chat_message("user"):
        st.markdown(user_prompt)

    # Build file context
    file_context = ""
    for filename, file_data in st.session_state.uploaded_files.items():
        try:
            file_obj = file_data['file']
            ftype = file_data['details']['filetype']
            
            # Reset file pointer to beginning
            file_obj.seek(0)
            
            if ftype == "text/plain":
                content = file_obj.read().decode("utf-8")
                file_context += f"\n[Fichier texte « {filename} » (extrait) :\n{content[:1500]}…]\n"
            elif "spreadsheetml" in ftype or ftype == "application/vnd.ms-excel":
                file_obj.seek(0)
                df = pd.read_excel(file_obj)
                file_context += f"\n[Fichier Excel « {filename} » — {len(df)} lignes. Aperçu :\n{df.head().to_markdown()}]\n"
            elif ftype == "text/csv":
                file_obj.seek(0)
                df = pd.read_csv(file_obj)
                file_context += f"\n[Fichier CSV « {filename} » — {len(df)} lignes. Aperçu :\n{df.head().to_markdown()}]\n"
            elif ftype == "application/pdf":
                file_obj.seek(0)
                reader = PdfReader(file_obj)
                pdf_text = ""
                for page in reader.pages:
                    pdf_text += page.extract_text() + "\n"
                file_context += f"\n[Fichier PDF « {filename} » ({len(reader.pages)} pages) (extrait) :\n{pdf_text[:1500]}…]\n"
            elif ftype == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                file_obj.seek(0)
                doc = Document(file_obj)
                doc_text = "\n".join([para.text for para in doc.paragraphs])
                file_context += f"\n[Fichier Word « {filename} » (extrait) :\n{doc_text[:1500]}…]\n"
            elif ftype == "application/vnd.openxmlformats-officedocument.presentationml.presentation":
                file_obj.seek(0)
                prs = Presentation(file_obj)
                ppt_text = ""
                for slide in prs.slides:
                    for shape in slide.shapes:
                        if hasattr(shape, "text"):
                            ppt_text += shape.text + "\n"
                file_context += f"\n[Fichier PowerPoint « {filename} » ({len(prs.slides)} diapositives) (extrait) :\n{ppt_text[:1500]}…]\n"
        except Exception as e:
            file_context += f"\n[Impossible de lire « {filename} » : {str(e)}]\n"

    api_messages = [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
    if file_context:
        api_messages[-1]["content"] += f"\n\nContexte des fichiers importés :\n{file_context}"

    with st.spinner("Mars réfléchit…"):
        start_time = time.time()
        assistant_response = call_groq_api(api_messages, st.session_state.model)
        response_time = time.time() - start_time

    assistant_response += f"\n\n⏱️ Réponse générée en {response_time:.2f}s"
    st.session_state.messages.append({"role": "assistant", "content": assistant_response})

    with st.chat_message("assistant"):
        st.markdown(assistant_response)

# Footer
st.markdown("---")
st.caption("Mars AI Assistant · Propulsé par Groq")
