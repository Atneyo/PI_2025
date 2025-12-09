from typing import Annotated
from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

app = FastAPI()


RESULT_PATH = "result.webm"

# Autorise all origins so frontend can call backend (maybe change origin to ["http://localhost:3000"] to increase security)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/outputs", StaticFiles(directory="outputs"), name="outputs")

@app.post("/analyze-video/")
async def analyze_video(files: list[UploadFile]):
    
    if not files:
        return {"error": "No video provided"}
    
    video = files[0]
    video_path = f"uploads/{video.filename}" # save video at this path
    
    # save file
    with open(video_path, "wb") as f:
        f.write(await video.read())

    # call YOLO on video_path
    
    
    video_url = f"http://127.0.0.1:8000/outputs/{RESULT_PATH}"
    
    return  video_url
