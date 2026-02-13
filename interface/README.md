# Application

## Frontend Installation and Launch

From the root of the repo:

```
cd interface/frontend
npm install
npm run dev
```

If you have access issues try deleting `node_modules` repertory before `npm install` command.

## Backend Installation and Launch

From the root of the repo.
Requirements :
```
pip install -r interface/backend/requirements_backend.txt   //backend
pip install -r models/speech_to_text/requirements_stt.txt   //stt
pip install -r monitoring/requirements.txt                  // monitoring
pip install -r interface/backend/requirements_cv.txt           // YOLO with HAT
pip install -r interface/backend/requirements_yolo_without_hat.txt   // YOLO without HAT
```

From the root of the repo:
```
uvicorn interface.backend.main:app --reload
```

### Using Docker

Launch the application from the root of the repo:
```
docker-compose up --build
```

The app is available at:
```
http://localhost:5173/
```

To clean up:
```
docker-compose down -v
docker rmi backend-image:latest frontend-image:latest
```

## File types supported by the application

The list of supported file types depends on the browser being used.

For use with Firefox, see a more detailed list at the following link: `https://support.mozilla.org/en-US/kb/audio-and-video-firefox`.

Here is a list of standard file types compatible with most configurations:
- For audio files:
| Format | Extension |
| ------ | --------- |
| MP3    | `.mp3`    |
| WAV    | `.wav`    |
| OGG    | `.ogg`    |
| AAC    | `.aac`    |
| FLAC   | `.flac`   |

- For video files:
| Format | Extension |
| ------ | --------- |
| MP4    | `.mp4`    |
| WebM   | `.webm`   |
| Ogg    | `.ogv`    |
| AVI    | `.avi`    |
| MOV    | `.mov`    |
| MKV    | `.mkv`    |
