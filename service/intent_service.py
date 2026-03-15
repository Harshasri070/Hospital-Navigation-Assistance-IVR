import spacy

nlp = spacy.load("en_core_web_sm")

INTENT_KEYWORDS = {
    "cardiology": [
        "cardio", "heart", "cardiology", "cardiologist"
    ],

    "neurology": [
        "neuro", "brain", "neurology", "neurologist"
    ],

    "emergency": [
        "emergency", "urgent", "accident", "critical", "ambulance"
    ],

    "pharmacy": [
        "pharmacy", "medicine", "drug", "tablet", "medical", "medicine shop"
    ]
}

def detect_intent(text):

    doc = nlp(text.lower())

    for intent, keywords in INTENT_KEYWORDS.items():
        for token in doc:
            if token.lemma_ in keywords:
                return intent

    return "unknown"