# main.py

from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from ivr_config import IVR_CONFIG
import uuid
import shutil

# IVR AI services
from service.stt_service import speech_to_text
from service.tts_service import text_to_speech
from utils.language_handler import detect_language
from service.entity_service import extract_entities
from service.dialogue_manager import generate_response
from service.translation_service import translate_to_english, translate_from_english

app = FastAPI()

# Enable CORS (for web simulator)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory session storage
sessions = {}

# Request Models
class StartCallRequest(BaseModel):
    caller_number: str = "Web Simulator"

class InputRequest(BaseModel):
    session_id: str
    text: str
def detect_intent(user_text: str):
    text = user_text.lower()

    if "opd" in text:
        return "opd"
    if "cardio" in text:
        return "cardiology"
    if "neuro" in text:
        return "neurology"
    if "emergency" in text:
        return "emergency"
    if "pharmacy" in text:
        return "pharmacy"
    if "direction" in text or "parking" in text:
        return "directions"

    return None


# =========================
# 1️⃣ Start Call (Welcome Prompt)
# =========================
@app.post("/ivr/start")
def start_call(request: StartCallRequest):

    session_id = str(uuid.uuid4())

    sessions[session_id] = {
        "current_menu": "welcome",
        "history": []
    }

    return {
        "session_id": session_id,
        "prompt": IVR_CONFIG["welcome"]["prompt"],
        "menu": "welcome"
    }


# =========================
# 2️⃣ Menu Handling Logic
# =========================


@app.post("/ivr/voice")
async def handle_voice(session_id: str, audio: UploadFile = File(...)):

    # 1️⃣ Check session
    session = sessions.get(session_id)
    if not session:
        return {"error": "Invalid session"}

    # 2️⃣ Save uploaded audio
    audio_path = f"temp_{audio.filename}"

    with open(audio_path, "wb") as buffer:
        shutil.copyfileobj(audio.file, buffer)

    # 3️⃣ Speech to Text
    user_text = speech_to_text(audio_path)

    if not user_text:
        response_text = "Sorry, I could not hear you clearly. Please repeat."
        audio_response = text_to_speech(response_text)

        return {
            "recognized_text": "",
            "intent": None,
            "audio_file": audio_response
        }
    print("Recognized text:", user_text)
    

    # 4️⃣ Language detection
    language = detect_language(user_text)

    # Debug: print detected language
    print("Detected language:", language)

    # normalize language code (important)
    language = language.split("-")[0]

    # 5️⃣ Translate user text → English
    english_text = translate_to_english(user_text, language)

    # Debug prints
    print("Original text:", user_text)
    print("Translated text:", english_text)
    print("Detected language:", language)

    # 6️⃣ Intent detection (use English text)
    intent = detect_intent(english_text)

    # 7️⃣ Entity extraction
    entities = extract_entities(english_text)

    # 8️⃣ Dialogue manager
    response_text = generate_response(intent, entities)

    # update session state
    session["current_menu"] = intent
    session["history"].append({
        "user": user_text,
        "intent": intent,
        "entities": entities
    })

    # 9️⃣ Fallback logic
    if not response_text:
        response_text = (
            "Sorry, I did not understand. "
            "Please say pharmacy, cardiology, emergency, or neurology."
        )

    # 🔟 Translate response back to user's language
    response_text = translate_from_english(response_text, language)

    # 1️⃣1️⃣ Text to Speech (use detected language)
    audio_response = text_to_speech(response_text, language)

    # 1️⃣2️⃣ Return response
    return {
        "recognized_text": user_text,
        "language": language,
        "intent": intent,
        "entities": entities,
        "menu": session["current_menu"],
        "response_text": response_text,
        "audio_file": audio_response
    }

# =========================
# Health Check
# =========================
@app.get("/")
def root():
    return {"message": "Hospital Navigation IVR Backend Running Successfully"}