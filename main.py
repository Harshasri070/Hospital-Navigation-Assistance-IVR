# main.py

from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uuid
import shutil
import os

# IVR config
from ivr_config import IVR_CONFIG

# Services
from service.stt_service import speech_to_text
from service.tts_service import text_to_speech
from service.entity_service import extract_entities
from service.dialogue_manager import generate_response
from service.translation_service import translate_to_english, translate_from_english

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files
app.mount("/audio_responses", StaticFiles(directory="audio_responses"), name="audio")
app.mount("/static", StaticFiles(directory="frontend"), name="static")

# Home
@app.get("/")
async def serve_home():
    return FileResponse("frontend/index.html")

# Session store
sessions = {}

# Models
class StartCallRequest(BaseModel):
    caller_number: str = "Web Simulator"

class InputRequest(BaseModel):
    session_id: str
    text: str


# =========================
# START CALL
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
# TEXT INPUT
# =========================
@app.post("/ivr/text")
async def handle_text(request: InputRequest):

    session = sessions.get(request.session_id)

    if not session:
        return {"response_text": "Invalid session", "audio_file": None}

    user_text = request.text
    text_lower = user_text.lower().strip()

    print("TEXT:", user_text)

    # 🔹 Language detection
    language = "en"

    if any('\u0C00' <= ch <= '\u0C7F' for ch in user_text):
        language = "te"
    elif any('\u0900' <= ch <= '\u097F' for ch in user_text):
        language = "hi"
    elif any(word in text_lower for word in ["ekkada", "undi"]):
        language = "te"
    elif any(word in text_lower for word in ["kaha", "hai"]):
        language = "hi"

        print("RAW TEXT:", user_text)

    # 🔹 Translation
    if language == "en":
        processed_text = user_text
    else:
        try:
            processed_text = translate_to_english(user_text, language)
        except:
            processed_text = user_text

    text_lower = processed_text.lower()

    # 🔥 Normalize speech errors
    text_lower = text_lower.replace("i see you", "icu")
    text_lower = text_lower.replace("obd", "opd")

    # 🔹 Intent detection
    if "opd" in text_lower:
        intent = "opd"
    elif "cardio" in text_lower:
        intent = "cardiology"
    elif "neuro" in text_lower:
        intent = "neurology"
    elif "radio" in text_lower:
        intent = "radiology"
    elif "patho" in text_lower:
        intent = "pathology"
    elif "icu" in text_lower:
        intent = "icu"
    elif "ward" in text_lower:
        intent = "general ward"
    elif "operation" in text_lower or "theatre" in text_lower:
        intent = "operation theater"
    elif "maternity" in text_lower:
        intent = "maternity"
    elif "isolation" in text_lower:
        intent = "isolation"
    elif "emergency" in text_lower:
        intent = "emergency"
    elif "pharmacy" in text_lower:
        intent = "pharmacy"
    elif "where" in text_lower or "direction" in text_lower:
        intent = "directions"
    else:
        intent = None

    print("INTENT:", intent)

    # 🔹 Generate response
    response_text = generate_response(intent, [])

    if not response_text:
        response_text = "Sorry, please say OPD, pharmacy, emergency or directions."

    # 🔹 Translate back
    if language != "en":
        try:
            translated = translate_from_english(response_text, language)
            if translated:
                response_text = translated
        except Exception as e:
            print("Translation error:", e)

    # 🔹 TTS
    audio_response = text_to_speech(response_text, language)
    audio_filename = os.path.basename(audio_response)

    return {
        "response_text": response_text,
        "audio_file": f"audio_responses/{audio_filename}"
    }


# =========================
# VOICE INPUT
# =========================
from fastapi import UploadFile, File
import shutil
import os

@app.post("/ivr/voice")
async def handle_voice(session_id: str, audio: UploadFile = File(...)):
    try:
        # 1️⃣ Validate session
        session = sessions.get(session_id)
        if not session:
            return {"response_text": "Invalid session", "audio_file": None}

        # 2️⃣ Save audio file
        audio_path = f"temp_{audio.filename}"
        with open(audio_path, "wb") as buffer:
            shutil.copyfileobj(audio.file, buffer)

        # 3️⃣ Speech to Text
        user_text = speech_to_text(audio_path)

        if not user_text:
            response_text = "Sorry, I could not hear you clearly. Please repeat."
            audio_response = text_to_speech(response_text, "en")

            return {
                "response_text": response_text,
                "audio_file": f"audio_responses/{os.path.basename(audio_response)}"
            }

        print("🎤 Recognized:", user_text)

        # =====================================================
        # 4️⃣ LANGUAGE DETECTION 
        # =====================================================
        text_lower = user_text.lower()
        language = "en"

        # 🔥 Telugu script 
        if any('\u0C00' <= ch <= '\u0C7F' for ch in user_text):
            language = "te"

        # 🔥 Hindi script
        elif any('\u0900' <= ch <= '\u097F' for ch in user_text):
            language = "hi"

        # 🔥 Telugu written in English
        elif any(word in text_lower for word in [
            "ekkada", "undi", "kavali", "cheppu"
        ]):
            language = "te"

        # 🔥 Hindi written in English
        elif any(word in text_lower for word in [
            "kaha", "hai", "kidhar", "kaise"
        ]):
            language = "hi"

        # 🔥 English medical keywords
        elif any(word in text_lower for word in [
            "opd","emergency","cardiology","neurology",
            "radiology","pathology","icu","pharmacy",
            "maternity","ward"
        ]):
            language = "en"

        print("🌐 Detected Language:", language)

        # =====================================================
        # 5️⃣ TRANSLATION → ENGLISH (FOR INTENT)
        # =====================================================
        if language == "en":
            processed_text = user_text
        else:
            try:
                processed_text = translate_to_english(user_text, language)
                print("🌍 Translated:", processed_text)
            except:
                processed_text = user_text

        # =====================================================
        # 6️⃣ CLEAN TEXT 
        # =====================================================
        text_lower = processed_text.lower().strip()

        # 🔥 Fix speech mistakes
        text_lower = text_lower.replace("i see you", "icu")
        text_lower = text_lower.replace("eye see you", "icu")
        text_lower = text_lower.replace("obd", "opd")
        text_lower = text_lower.replace("emargency", "emergency")

        print("🧠 Final Text:", text_lower)

        # =====================================================
        # 7️⃣ INTENT DETECTION 
        # =====================================================
        if "opd" in text_lower:
            intent = "opd"
        elif "cardiology" in text_lower:
            intent = "cardiology"
        elif "neurology" in text_lower:
            intent = "neurology"
        elif "radiology" in text_lower:
            intent = "radiology"
        elif "pathology" in text_lower:
            intent = "pathology"
        elif "icu" in text_lower:
            intent = "icu"
        elif "general ward" in text_lower:
            intent = "general ward"
        elif "operation" in text_lower or "theater" in text_lower:
            intent = "operation theater"
        elif "maternity" in text_lower:
            intent = "maternity"
        elif "isolation" in text_lower:
            intent = "isolation"
        elif "emergency" in text_lower:
            intent = "emergency"
        elif "pharmacy" in text_lower:
            intent = "pharmacy"
        elif "direction" in text_lower or "where" in text_lower:
            intent = "directions"
        else:
            intent = None

        intent = intent.strip().lower() if intent else None

        print("🎯 Intent:", intent)

        # =====================================================
        # 8️⃣ ENTITY EXTRACTION
        # =====================================================
        entities = extract_entities(processed_text)

        # =====================================================
        # 9️⃣ RESPONSE GENERATION
        # =====================================================
        response_text = generate_response(intent, entities)

        if not response_text:
            response_text = "Sorry, I did not understand. Please say OPD, emergency, or pharmacy."

        print("💬 Response:", response_text)

        # =====================================================
        # 🔟 TRANSLATE BACK 
        # =====================================================
        if language != "en":
            try:
                response_text = translate_from_english(response_text, language)
                print("🔁 Translated Back:", response_text)
            except Exception as e:
                print("Translation error:", e)

        # =====================================================
        # 1️⃣1️⃣ TEXT TO SPEECH
        # =====================================================
        audio_response = text_to_speech(response_text, language)
        audio_filename = os.path.basename(audio_response)

        # =====================================================
        # 1️⃣2️⃣ UPDATE SESSION
        # =====================================================
        session["current_menu"] = intent
        session["history"].append({
            "user": user_text,
            "intent": intent,
            "entities": entities
        })

        # =====================================================
        # ✅ FINAL RESPONSE
        # =====================================================
        return {
            "recognized_text": user_text,
            "language": language,
            "intent": intent,
            "entities": entities,
            "menu": session["current_menu"],
            "response_text": response_text,
            "audio_file": f"audio_responses/{audio_filename}"
        }

    except Exception as e:
        print("🔥 ERROR:", str(e))
        return {
            "response_text": "Server error occurred",
            "audio_file": None
        }