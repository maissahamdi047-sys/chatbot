import os
import streamlit as st
from dotenv import load_dotenv
import google.generativeai as genai
from datetime import datetime
import pytz
import pandas as pd
import base64
from PIL import Image
import time

# Load environment variables
load_dotenv()

# Configure Streamlit page settings
st.set_page_config(
    page_title="Mars AI Assistant",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)


def inject_custom_css():
    st.markdown("""
    <style>
        .stApp {
            display: flex;
            flex-direction: column;
            min-height: 100vh;
        }
        .main .block-container {
            flex: 1;
            padding-bottom: 100px;
        }
        .stChatMessage {
            border-radius: 18px;
            padding: 16px 20px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.1);
            margin-bottom: 12px;
        }
        [data-testid="stChatMessage"] [data-testid="chatAvatarIcon-user"] {
            background: linear-gradient(135deg, #667eea, #764ba2);
        }
        [data-testid="stChatMessage"] [data-testid="chatAvatarIcon-assistant"] {
            background: linear-gradient(135deg, #ff758c, #ff7eb3);
        }
        .stTextInput > div > div > input {
            background-color: rgba(255,255,255,0.15);
            color: white;
            border-radius: 15px;
            padding: 12px 18px;
            border: none;
            font-size: 16px;
        }
        .stButton > button {
            border-radius: 12px;
            font-weight: 600;
        }
    </style>
    """, unsafe_allow_html=True)


inject_custom_css()

# ── Google Gemini configuration ───────────────────────────────────────────────
GOOGLE_API_KEY = os.getenv("GEMINI_API_KEY", "")

if not GOOGLE_API_KEY:
    st.warning("⚠️ Clé API Gemini manquante. Définissez `GEMINI_API_KEY` dans votre fichier `.env`.")
else:
    genai.configure(api_key=GOOGLE_API_KEY)

# Modèles Gemini disponibles (juin 2025)
GEMINI_MODELS = {
    "Gemini 2.0 Flash (Recommandé)": "gemini-2.0-flash",
    "Gemini 1.5 Flash": "gemini-1.5-flash",
    "Gemini 1.5 Pro": "gemini-1.5-pro",
}

SYSTEM_INSTRUCTION = (
    "Tu es Mars, un assistant IA intelligent et bienveillant. "
    "Tu réponds en français si la question est en français, en anglais sinon. "
    "Tu es précis, honnête et utile."
)

# ── Session state ─────────────────────────────────────────────────────────────
if "selected_gemini_model" not in st.session_state:
    st.session_state.selected_gemini_model = "gemini-2.0-flash"
if "chat_session" not in st.session_state and GOOGLE_API_KEY:
    model = genai.GenerativeModel(
        model_name=st.session_state.selected_gemini_model,
        system_instruction=SYSTEM_INSTRUCTION
    )
    st.session_state.chat_session = model.start_chat(history=[])
if "conversation_started" not in st.session_state:
    st.session_state.conversation_started = datetime.now(pytz.utc)
if "temperature" not in st.session_state:
    st.session_state.temperature = 0.7


def reset_chat_session():
    """Recreate the chat session with the currently selected model."""
    if GOOGLE_API_KEY:
        model = genai.GenerativeModel(
            model_name=st.session_state.selected_gemini_model,
            system_instruction=SYSTEM_INSTRUCTION,
            generation_config=genai.types.GenerationConfig(
                temperature=st.session_state.temperature,
                max_output_tokens=2048,
            )
        )
        st.session_state.chat_session = model.start_chat(history=[])


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("⚙️ Paramètres Mars")

    # Model selection
    selected_label = st.selectbox(
        "Modèle Gemini",
        options=list(GEMINI_MODELS.keys()),
        index=0,
        key="gemini_model_select"
    )
    new_model_id = GEMINI_MODELS[selected_label]
    if new_model_id != st.session_state.selected_gemini_model:
        st.session_state.selected_gemini_model = new_model_id
        reset_chat_session()
        st.rerun()

    # Temperature
    new_temp = st.slider(
        "Créativité",
        min_value=0.1,
        max_value=1.0,
        value=st.session_state.temperature,
        step=0.1,
        help="Plus élevé = réponses plus créatives"
    )
    if new_temp != st.session_state.temperature:
        st.session_state.temperature = new_temp
        reset_chat_session()

    # Conversation stats
    st.divider()
    st.subheader("📊 Statistiques")
    duration = datetime.now(pytz.utc) - st.session_state.conversation_started
    st.write(f"⏱️ Durée : {duration.seconds // 60}m {duration.seconds % 60}s")
    if GOOGLE_API_KEY and "chat_session" in st.session_state:
        msg_count = len([m for m in st.session_state.chat_session.history if m.role == "user"])
        st.write(f"💬 Messages utilisateur : {msg_count}")

    st.divider()
    if st.button("🗑️ Effacer la conversation"):
        reset_chat_session()
        st.session_state.conversation_started = datetime.now(pytz.utc)
        st.rerun()

# ── Main interface ─────────────────────────────────────────────────────────────
st.title("🤖 Mars AI Assistant")
st.caption(f"Modèle actif : **{selected_label}**")

if not GOOGLE_API_KEY:
    st.error("Impossible de démarrer sans clé API Gemini. Ajoutez `GEMINI_API_KEY=<votre_clé>` dans `.env`.")
    st.stop()

# Display chat history
for message in st.session_state.chat_session.history:
    role = "assistant" if message.role == "model" else "user"
    with st.chat_message(role):
        st.markdown(message.parts[0].text)

# Quick actions
st.markdown("**Actions rapides :**")
col1, col2, col3 = st.columns(3)
if col1.button("📝 Résumer"):
    with st.chat_message("assistant"):
        with st.spinner("Résumé en cours…"):
            resp = st.session_state.chat_session.send_message("Fais un résumé concis de notre conversation.")
            st.markdown(resp.text)
if col2.button("💡 Idées créatives"):
    with st.chat_message("assistant"):
        with st.spinner("Génération d'idées…"):
            resp = st.session_state.chat_session.send_message("Propose 3 idées créatives en rapport avec notre échange.")
            st.markdown(resp.text)
if col3.button("🔍 Expliquer simplement"):
    with st.chat_message("assistant"):
        with st.spinner("Simplification…"):
            resp = st.session_state.chat_session.send_message("Explique le dernier concept abordé de façon très simple.")
            st.markdown(resp.text)

# Chat input
user_input = st.chat_input("Écrire un message à Mars…")

if user_input:
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.spinner("Mars réfléchit…"):
            try:
                start = time.time()
                response = st.session_state.chat_session.send_message(user_input)
                elapsed = time.time() - start
                st.markdown(response.text)
                st.caption(f"⏱️ {elapsed:.2f}s")
            except Exception as e:
                st.error(f"Erreur : {str(e)}")

# Footer
st.markdown("---")
st.caption("Mars AI Assistant · Propulsé par Google Gemini")
