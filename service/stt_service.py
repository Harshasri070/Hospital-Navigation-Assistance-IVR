import whisper

model = whisper.load_model("medium")

def speech_to_text(audio_path):

    result = model.transcribe(audio_path, fp16=False)

    print("RAW STT:", result)

    return result["text"]