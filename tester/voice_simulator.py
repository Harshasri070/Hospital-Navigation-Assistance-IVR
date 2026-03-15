import sounddevice as sd
import soundfile as sf

def record_voice(filename="input.wav", duration=5):

    samplerate = 44100

    print("Recording...")

    recording = sd.rec(int(duration * samplerate), samplerate=samplerate, channels=1)

    sd.wait()

    sf.write(filename, recording, samplerate)

    print("Recording saved:", filename)

record_voice()