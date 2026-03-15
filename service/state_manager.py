import uuid

sessions = {}

def create_session():

    session_id = str(uuid.uuid4())

    sessions[session_id] = {
        "state": "welcome",
        "fail_count": 0,
        "history": []
    }

    return session_id

def get_session(session_id):

    return sessions.get(session_id)

def update_state(session_id, state):

    sessions[session_id]["state"] = state

def add_history(session_id, text):

    sessions[session_id]["history"].append(text)