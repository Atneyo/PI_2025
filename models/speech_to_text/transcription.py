import whisper
import time
import os
import json

def transcribe(file, model_name="base",output_dir="interface/backend/outputs/stt"):
    # loading model
    start_load = time.time()
    model = whisper.load_model(model_name)
    end_load = time.time()
    load_time = end_load-start_load

    # transcription
    start_transcribe = time.time()
    result = model.transcribe(file)
    end_transcribe = time.time()
    transcription_time = end_transcribe-start_transcribe

    # statistics
    stats = {}
    stats["load_time"]=load_time
    stats["transcription_time"]=transcription_time
    stats["total_process_time"]=load_time+transcription_time
    stats["model_used"]=model_name

    file_name = os.path.splitext(os.path.basename(file))[0]
    # create outputs dir
    output_dir = os.path.join(output_dir, file_name)
    os.makedirs(output_dir, exist_ok=True)
    
    txt_path = os.path.join(output_dir, f"{file_name}.txt")
    json_path = os.path.join(output_dir, f"{file_name}.json")
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(result["text"])
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=4)

    return result["text"], stats

if '__main__'==__name__:
    result = transcribe("test_poeme_anglais.wav",model="tiny")
    print(result)