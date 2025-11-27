from vosk import Model, KaldiRecognizer
import wave, json, sys

wf = wave.open("test_poeme_anglais.wav", "rb")
model = Model("vosk-model-small-fr-0.22")
rec = KaldiRecognizer(model, wf.getframerate())

while True:
    data = wf.readframes(4000)
    if len(data) == 0:
        break
    if rec.AcceptWaveform(data):
        print(json.loads(rec.Result()))

print(json.loads(rec.FinalResult()))
