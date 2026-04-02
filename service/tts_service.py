from gtts import gTTS
import uuid
import os

OUTPUT_FOLDER = "audio_responses"

os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Supported language mapping
LANGUAGE_MAP = {
    "en": "en",
    "hi": "hi",
    "te": "te"
}

def text_to_speech(text, lang="en"):

    # normalize language
    lang = LANGUAGE_MAP.get(lang, "en")

    filename = f"{uuid.uuid4()}.mp3"
    filepath = os.path.join(OUTPUT_FOLDER, filename)

    tts = gTTS(text=text, lang=lang)
    tts.save(filepath)

    print("Saved audio at:", filepath)
    print("File exists:", os.path.exists(filepath))

    return filepath