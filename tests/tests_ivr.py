from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

# ✅ UNIT TEST
def test_root():
    res = client.get("/")
    assert res.status_code == 200


# ✅ SESSION CREATION
def test_create_session():
    res = client.post("/ivr/session", params={"call_id": "test123"})
    assert res.status_code == 200


# ✅ INTEGRATION TEST (Hospital Flow)
def test_hospital_navigation_flow():
    call_id = "hospital_001"

    # Step 1: Create session
    client.post("/ivr/session", params={"call_id": call_id})

    # Step 2: User asks for department
    res = client.post("/conversation_flow", params={
        "call_id": call_id,
        "user_text": "I need cardiology department"
    })

    assert res.status_code == 200
    assert "cardiology" in res.text.lower()


# ✅ MULTI-STEP FLOW
def test_next_step_flow():
    call_id = "hospital_002"

    client.post("/ivr/session", params={"call_id": call_id})

    client.post("/conversation_flow", params={
        "call_id": call_id,
        "user_text": "Book appointment"
    })

    res = client.post("/next_step", params={
        "call_id": call_id,
        "user_text": "Neurology"
    })

    assert res.status_code == 200


# ✅ E2E TEST (Full IVR Flow)
def test_full_ivr_flow():
    res = client.get("/ivr/start")
    assert res.status_code == 200

    res = client.post("/handle_key", params={
        "Digits": "1",
        "menu": "main-menu"
    })

    assert res.status_code == 200


# ✅ ERROR HANDLING
def test_invalid_input():
    res = client.post("/conversation_flow", params={
        "call_id": "test",
        "user_text": ""
    })

    assert res.status_code in [200, 422]