# main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from ivr_config import IVR_CONFIG
import uuid

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
@app.post("/ivr/input")
def handle_input(request: InputRequest):

    session = sessions.get(request.session_id)

    if not session:
        return {"error": "Invalid session"}

    intent = detect_intent(request.text)

    if not intent:
        return {
            "status": "unknown",
            "prompt": "Sorry, I did not understand. Please say OPD, Emergency, Pharmacy, or Directions."
        }

    if intent in IVR_CONFIG:
        return {
            "status": "ok",
            "menu": intent,
            "prompt": IVR_CONFIG[intent]["prompt"]
        }

    return {
        "status": "error",
        "prompt": "Something went wrong."
    }

    option = menu_data["options"][request.digit]
    action = option["action"]

    # =====================
    # Action: GOTO (Menu Navigation)
    # =====================
    if action == "goto":
        target_menu = option["target"]
        session["current_menu"] = target_menu

        return {
            "status": "ok",
            "menu": target_menu,
            "prompt": IVR_CONFIG[target_menu]["prompt"]
        }

    # =====================
    # Action: END (Call Termination)
    # =====================
    elif action == "end":
        message = option["message"]
        del sessions[request.session_id]

        return {
            "status": "hangup",
            "action": "hangup",
            "message": message
        }


# =========================
# Health Check
# =========================
@app.get("/")
def root():
    return {"message": "Hospital Navigation IVR Backend Running Successfully"}