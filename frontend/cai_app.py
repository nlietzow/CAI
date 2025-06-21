import re
import io
import streamlit as st
import streamlit.components.v1 as components
import vertexai
from vertexai.generative_models import GenerativeModel, Part
from audiorecorder import audiorecorder
from streamlit_extras.stylable_container import stylable_container
import json
import requests

# --- Configuration ---
# TODO: Please replace these with your actual project IDs and locations
PROJECT_ID = "hack-thelaw25cam-572"
LOCATION = "global"

USER_ID = "user-345"
BASE_URL = "https://api.mehr-als-nur-recht.de"
APP_NAME = "strategy_agent"

# Initialize Vertex AI
try:
    vertexai.init(project=PROJECT_ID, location=LOCATION)
except Exception as e:
    st.error(f"Error initializing Vertex AI: {e}")
    st.stop()

# Initialize the Gemini model
model = GenerativeModel('gemini-2.5-flash-lite-preview-06-17')


def init_session(user_id: str):
    url = f"{BASE_URL}/apps/{APP_NAME}/users/{user_id}/sessions"
    print(url)
    payload = json.dumps({})
    headers = {
        'accept': 'application/json',
        'Content-Type': 'application/json'
    }
    r = requests.request("POST", url, headers=headers, data=payload)
    r.raise_for_status()
    return r.json().get("id")


def send_message_to_session(prompt: str, session_id: str, user_id: str):
    url = f"{BASE_URL}/run"
    payload = json.dumps({
        "appName": "strategy_agent",
        "userId": user_id,
        "sessionId": session_id,
        "newMessage": {
            "role": "user",
            "parts": [
                {
                    "text": prompt
                }
            ]
        },
        "streaming": False
    })
    headers = {
        'Content-Type': 'application/json'
    }

    r = requests.request("POST", url, headers=headers, data=payload)
    r.raise_for_status()

    contents = r.json()
    try:
        text = contents[-1]["content"]["parts"][0]["text"]
    except:
        text = "An error occurred while processing your request. Please try again later."

    updated_text = re.sub(
        r'\b((?:IDS|ICSID)-\d+)\b',
        r'[\1](https://jusmundi.com/en/search?query=\1&#page=1&lang=en)',
        text
    )

    yield updated_text


def handle_prompt(prompt):
    """Processes a user prompt (text) and interacts with the chat model."""
    # Add user message to history and display it
    st.session_state.chat_history.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="🧑‍⚖️"):
        st.markdown(prompt)

    # Send the message to the Gemini model and stream the response
    with st.chat_message("CAI"):
        response_stream = send_message_to_session(
            prompt,
            st.session_state.chat_session,
            USER_ID
        )

        placeholder = st.empty()
        full_text = ""
        for chunk in response_stream:
            full_text += chunk
            placeholder.markdown(full_text + "▌", unsafe_allow_html=True)

        placeholder.markdown(full_text, unsafe_allow_html=True)
        st.session_state.chat_history.append({"role": "model", "content": full_text})


# --- Streamlit UI ---
st.set_page_config(page_title="CAI - Co-Counsel AI", page_icon="🤖", layout="wide")

# Load and display the HTML logo in the main area
try:
    with open("logo.html", "r") as f:
        logo_html = f.read()
    components.html(logo_html, height=150)
except FileNotFoundError:
    st.warning("logo.html not found.")

# Arrange main title and FAQ button in columns
col1, col2 = st.columns([0.95, 0.05])

with col1:
    st.title("CAI: Your Strategic Co-Counsel")

with col2:
    # Spacer for better alignment
    st.write("")
    if st.button("FAQ"):
        try:
            with open("faq.md", "r", encoding="utf-8") as f:
                faq_content = f.read()


            @st.dialog("Frequently Asked Questions")
            def show_faq():
                st.markdown(faq_content)


            show_faq()

        except FileNotFoundError:
            st.error("faq.md not found.")
st.caption("Out-think. Out-prepare. Out-win.")

# Initialize chat history in Streamlit session state if it doesn't exist
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "last_audio_raw_data" not in st.session_state:
    st.session_state.last_audio_raw_data = None

# LEGACY: Initialize chat session in the model
# Start the chat conversation in the model
# if "chat_session" not in st.session_state:
#    st.session_state.chat_session = model.start_chat(history=[])

# Start the chat conversation in the model
if "chat_session" not in st.session_state:
    st.session_state.chat_session = init_session(USER_ID)
    print(f"Initialized chat session: {st.session_state.chat_session}")

# Display previous chat messages
for message in st.session_state.chat_history:
    if message["role"] == "user":
        with st.chat_message("user", avatar="🧑‍⚖️"):
            st.markdown(message["content"])
    else:
        with st.chat_message("CAI"):
            st.markdown(message["content"], unsafe_allow_html=True)

# --- Input Methods ---

with stylable_container(
        key="bottom_content",
        css_styles="""
            {
                position: fixed;
                bottom: 100px;
                right: 55px;
                width: 100px;
                background-color: transparent;
                padding: 1rem;
                border-radius: 15px;
                z-index: 1000;
            }
            """,
):
    audio_bytes = audiorecorder("🎙️", "⏹️", key="audio_recorder")

# Method 1: Text input (remains at the bottom)
text_prompt = st.chat_input("Enter your case summary and legal strategy here...")

# Input processing
if text_prompt:
    handle_prompt(text_prompt)
elif audio_bytes and len(audio_bytes) > 0:
    # Compare raw audio data to prevent reprocessing the same audio
    if audio_bytes.raw_data != st.session_state.get("last_audio_raw_data"):
        st.session_state.last_audio_raw_data = audio_bytes.raw_data
        with st.spinner("Transcribing audio..."):
            try:
                wav_io = io.BytesIO()
                audio_bytes.export(wav_io, format="wav")
                wav_bytes = wav_io.getvalue()

                audio_part = Part.from_data(data=wav_bytes, mime_type="audio/wav")

                # Send audio to Gemini for transcription
                response = model.generate_content(
                    ["Transcribe this audio:", audio_part],
                    stream=True
                )

                transcribed_text = ""
                for chunk in response:
                    transcribed_text += chunk.text
                transcribed_text = transcribed_text.strip()

                if transcribed_text:
                    handle_prompt(transcribed_text)
                else:
                    # If transcription fails or is empty, ask the user to repeat.
                    st.session_state.chat_history.append(
                        {"role": "model", "content": "I'm sorry, I couldn't understand the audio. Please try again."})
                    st.rerun()

            except Exception as e:
                st.error(f"Error during transcription: {e}")
