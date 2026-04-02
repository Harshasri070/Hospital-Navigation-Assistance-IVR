from sentence_transformers import SentenceTransformer, util

model = SentenceTransformer('all-MiniLM-L6-v2')

INTENTS = {
    "opd": "outpatient department",
    "cardiology": "heart department",
    "neurology": "brain department",
    "radiology": "scan xray department",
    "pathology": "lab blood test",
    "emergency": "emergency urgent care",
    "icu": "intensive care unit",
    "pharmacy": "medicine store",
    "directions": "where location help"
}

def detect_intent_ai(text):
    text_embedding = model.encode(text, convert_to_tensor=True)

    best_intent = None
    best_score = 0

    for intent, desc in INTENTS.items():
        score = util.cos_sim(text_embedding, model.encode(desc, convert_to_tensor=True))

        if score > best_score:
            best_score = score
            best_intent = intent

    if best_score > 0.4:
        return best_intent

    return None