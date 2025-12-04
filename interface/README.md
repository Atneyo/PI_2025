# Application

## Frontend Installation and Launch

From the root of the application:

```
cd frontend
npm install
npm run dev
```

### Using Docker

From the root of the application:

```
docker-compose up
```

The app is available at:

```
http://localhost:3000/
```

To stop Docker:

```
docker-compose down
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
