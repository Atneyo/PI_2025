import os
import sys
import wave
import json
import time
import subprocess

# Fichiers WAV à tester
FILES = {
    "fr": "audio/test_poeme.wav",
    "en": "audio/test_poeme_anglais.wav"
}

RESULTS_FILE = "results.txt"

# ---- Helper: conversion à 16 kHz mono (si nécessaire) ----
# def ensure_wav_16khz_mono(wav_file):
#     tmp_file = "tmp_" + wav_file
#     if not os.path.exists(tmp_file):
#         subprocess.run([
#             "ffmpeg", "-y", "-i", wav_file, "-ac", "1", "-ar", "16000", tmp_file
#         ])
#     return tmp_file

def ensure_wav_16khz_mono(wav_file):
    # dossier audio
    audio_dir = os.path.dirname(wav_file)
    base_name = os.path.basename(wav_file)
    tmp_file = os.path.join(audio_dir, "tmp_" + base_name)  # ex: audio/tmp_test_poeme.wav

    if not os.path.exists(tmp_file):
        print(f"[INFO] Converting {wav_file} -> {tmp_file} (16kHz mono)")
        subprocess.run([
            "ffmpeg", "-y", "-i", wav_file,
            "-ac", "1", "-ar", "16000", tmp_file
        ], check=True)
    else:
        print(f"[INFO] Temporary WAV already exists: {tmp_file}")

    return tmp_file

# ---- Whisper Tiny ----
def run_whisper(wav_file, lang_hint=None):
    try:
        import whisper
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "openai-whisper"])
        import whisper
    model = whisper.load_model("tiny")
    start = time.time()
    if lang_hint:
        result = model.transcribe(wav_file, language=lang_hint)
    else:
        result = model.transcribe(wav_file)
    end = time.time()
    return result["text"], end-start

# ---- Whisper Base ----
def run_whisper_base(wav_file, lang_hint=None):
    try:
        import whisper
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "openai-whisper"])
        import whisper
    model = whisper.load_model("base")
    start = time.time()
    if lang_hint:
        result = model.transcribe(wav_file, language=lang_hint)
    else:
        result = model.transcribe(wav_file)
    end = time.time()
    return result["text"], end-start

# ---- Vosk ----
def run_vosk(wav_file, lang):
    try:
        from vosk import Model, KaldiRecognizer
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "vosk"])
        from vosk import Model, KaldiRecognizer

    # Téléchargement modèles si absents
    if not os.path.exists("vosk-model-small-fr-0.22"):
        os.system("wget -q https://alphacephei.com/vosk/models/vosk-model-small-fr-0.22.zip -O fr.zip")
        os.system("unzip -q fr.zip && rm fr.zip")
    if not os.path.exists("vosk-model-small-en-us-0.15"):
        os.system("wget -q https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip -O en.zip")
        os.system("unzip -q en.zip && rm en.zip")

    model_path = "vosk-model-small-fr-0.22" if lang == "fr" else "vosk-model-small-en-us-0.15"
    wf = wave.open(wav_file, "rb")
    model = Model(model_path)
    rec = KaldiRecognizer(model, wf.getframerate())
    while True:
        data = wf.readframes(4000)
        if len(data) == 0: break
        rec.AcceptWaveform(data)
    return json.loads(rec.FinalResult())['text']

# ---- SpeechBrain (anglais uniquement) ----
def run_speechbrain(wav_file):
    try:
        from speechbrain.inference import EncoderDecoderASR
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "speechbrain==0.5.13 huggingface_hub==0.16.4"])
        from speechbrain.inference import EncoderDecoderASR
    model = EncoderDecoderASR.from_hparams(
        source="speechbrain/asr-crdnn-rnnlm-librispeech",
        savedir="tmp_asr"
    )
    start = time.time()
    text = model.transcribe_file(wav_file)
    end = time.time()
    return text, end-start

# ---- Main ----
if __name__ == "__main__":
    for lang, wav in FILES.items():
        if not os.path.exists(wav):
            print(f"[ERROR] File not found: {wav}")
            sys.exit(1)

    with open(RESULTS_FILE, "w") as f:
        f.write("=== STT Test for English & French WAVs ===\n")

        for lang, wav in FILES.items():
            f.write(f"\n=== Language: {lang.upper()} | File: {wav} ===\n")
            wav_16 = ensure_wav_16khz_mono(wav)

            # Whisper
            print(f"[INFO] Running Whisper ({lang})...")
            whisper_text, whisper_time = run_whisper(wav_16, lang_hint=lang)
            f.write(f"\n--- Whisper Tiny ---\n{whisper_text}\nTime: {whisper_time:.2f}s\n")

            # Whisper
            print(f"[INFO] Running Whisper Base ({lang})...")
            whisper_text, whisper_time = run_whisper_base(wav_16, lang_hint=lang)
            f.write(f"\n--- Whisper Base ---\n{whisper_text}\nTime: {whisper_time:.2f}s\n")

            # Vosk
            print(f"[INFO] Running Vosk ({lang})...")
            start = time.time()
            vosk_text = run_vosk(wav_16, lang)
            vosk_time = time.time() - start
            f.write(f"\n--- Vosk ---\n{vosk_text}\nTime: {vosk_time:.2f}s\n")

            # SpeechBrain (anglais uniquement)
            if lang == "en":
                print("[INFO] Running SpeechBrain (en)...")
                sb_text, sb_time = run_speechbrain(wav_16)
                f.write(f"\n--- SpeechBrain ---\n{sb_text}\nTime: {sb_time:.2f}s\n")

    print(f"[INFO] Done. Results saved in {RESULTS_FILE}")

