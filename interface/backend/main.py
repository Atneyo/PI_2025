from typing import Annotated
from contextlib import asynccontextmanager
from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.concurrency import run_in_threadpool
from models.speech_to_text.transcription import transcribe
import os
import json
import subprocess
from monitoring.detect_hailo import is_hailo_hat_present
if is_hailo_hat_present():
    from interface.backend.AI.yolo_detection import yolo_detection
from interface.backend.AI.yolo_detection_without_yolo import yolo_detection_without_yolo
# define life of the application
# The first part of the function, before the yield, will be executed before the application starts.
# And the part after the yield will be executed after the application has finished.
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Launch monitoring
    subprocess.Popen(["python3","monitoring/all_monitoring.py"])
    yield
    # Stop monitoring

app = FastAPI(lifespan=lifespan)


VIDEO_RESULT_PATH = "result.webm"

# Autorise all origins so frontend can call backend (maybe change origin to ["http://localhost:3000"] to increase security)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs("interface/backend/outputs",exist_ok=True)
app.mount("/outputs", StaticFiles(directory="interface/backend/outputs"), name="outputs")


# return video result url and global statistics
@app.post("/analyze-video/")
async def analyze_video(files: list[UploadFile], isHat: bool = Form(), fps: int = Form()):
    
    if not files:
        return {"error": "No video provided"}

    # check if uploads and outputs folders exist
    os.makedirs("interface/backend/uploads",exist_ok=True)
    # os.makedirs("outputs",exist_ok=True)
    

    video = files[0]
    video_path = f"interface/backend/uploads/{video.filename}" # save video at this path
    
    # save file
    with open(video_path, "wb") as f:
        f.write(await video.read())

    # call YOLO on video_path
    if isHat:
        if is_hailo_hat_present():
            recorded_path, stats = await run_in_threadpool(
                yolo_detection,
                live_input=False,
                video_path=video_path,
                frame_rate=fps,
                output_dir="interface/backend/outputs",
                record_filename=VIDEO_RESULT_PATH,
                hef_path="interface/backend/AI/yolov11n.hef",
            )
    else:
        recorded_path, stats = await run_in_threadpool(
            yolo_detection_without_yolo,
            live_input=False,
            video_path=video_path,
            frame_rate=fps,
            output_dir="interface/backend/outputs",
            record_filename=VIDEO_RESULT_PATH,
            yolo_path="interface/backend/AI/yolov11n.pt",
        )

    # delete input file to save memory
    os.remove(video_path)
    
    video_url = f"http://127.0.0.1:8000/outputs/{VIDEO_RESULT_PATH}"
    
    return  {"video": video_url, "recording_path": str(recorded_path), "stats": stats}

# return transcription and global statistics
@app.post("/analyze-audio/")
async def analyze_audio(files: list[UploadFile], model: str = Form("base")):
    
    if not files:
        return {"error": "No audio provided"}
    
    # check if uploads and outputs folders exist
    os.makedirs("interface/backend/uploads",exist_ok=True)
    # os.makedirs("outputs",exist_ok=True)
    

    audio = files[0]
    audio_path = f"interface/backend/uploads/{audio.filename}" # save audio at this path

    # save file
    with open(audio_path, "wb") as f:
        f.write(await audio.read())

    # call Whisper on audio_path
    audio_result, stats = await run_in_threadpool(transcribe, audio_path, model_name=model, output_dir="interface/backend/outputs/stt")

    # delete input file to save memory
    os.remove(audio_path)
    
    
    return  {"text": audio_result, "stats": stats}

# return current statistics from current detection, null if no detection
@app.get("/statistics-video/")
async def get_video_statistics():
    pass

# return current statistics from current transcription, null if no transcription
@app.get("/statistics-audio/")
async def get_audio_statistics():
    pass

# return monitoring information
@app.get("/monitoring/")
async def get_monitoring():
    with open("current_monitoring_data.json","r") as f:
        data = json.load(f)
    return data
