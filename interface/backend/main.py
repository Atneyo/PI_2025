from typing import Annotated
from contextlib import asynccontextmanager
from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from models.speech_to_text.transcription import transcribe
import os
import json
import subprocess

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
async def analyze_video(files: list[UploadFile]):
    
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
    

    # delete input file to save memory
    os.remove(video_path)
    
    video_url = f"http://127.0.0.1:8000/outputs/{VIDEO_RESULT_PATH}"
    
    return  {"video": video_url, "stats": {}}

# return transcription and global statistics
@app.post("/analyze-audio/")
async def analyze_audio(files: list[UploadFile]):
    
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
    audio_result = transcribe(audio_path)

    # delete input file to save memory
    os.remove(audio_path)
    
    
    return  {"text": audio_result, "stats": {}}

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
    with open("monitoring/current_monitoring_data.json","r") as f:
        data = json.load(f)
    return data