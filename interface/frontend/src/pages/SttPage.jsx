import { useState, useRef } from "react";
import { useNavigate } from "react-router-dom";
import "./SttPage.css";

function SttPage() {
  const navigate = useNavigate();
  const [model, setModel] = useState("whisper");
  const [audioFiles, setAudioFiles] = useState([]);
  const [transcriptionResult, setTranscriptionResult] = useState("");

  const fileInputRef = useRef(null);

  const handleFiles = (files) => {
    const filteredFiles = Array.from(files).filter(file =>
      file.type.startsWith("audio/")
    );
    setAudioFiles((prev) => [...prev, ...filteredFiles]);
  };

  const handleFileChange = (e) => {
    handleFiles(e.target.files);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    handleFiles(e.dataTransfer.files);
  };

  const handleDragOver = (e) => {
    e.preventDefault();
  };

  const handleAddFolder = () => {
    fileInputRef.current.click();
  };

  const handleTranscribe = () => {
    if (audioFiles.length === 0) {
      alert("Please select an audio file");
      return;
    }

    // Simulation for now
    const filenames = audioFiles.map(f => f.name).join(", ");
    setTranscriptionResult(
      `Simulated result for the model "${model}" on files: ${filenames}`
    );
  };

  return (
    <div className="container">
      <header className="app-header">
        <h1>Speech-to-Text Demo</h1>
        <button
          className="video-button"
          onClick={() => navigate("/video")} // redirect to /video
        >
          Video
        </button>
      </header>

      {/* Drag & Drop Zone */}
      <div
        className="drop-zone"
        onDrop={handleDrop}
        onDragOver={handleDragOver}
      >
        <p>Drag and drop audio files here</p>
        <button onClick={handleAddFolder}>Add Files</button>
        <input
          type="file"
          ref={fileInputRef}
          multiple
          style={{ display: "none" }}
          onChange={handleFileChange}
        />
      </div>

      <label>Select a model</label>
      <select value={model} onChange={(e) => setModel(e.target.value)}>
        <option value="whisper">Whisper</option>
        <option value="vosk">Vosk</option>
        <option value="wav2vec2">Wav2Vec2</option>
      </select>

      <button onClick={handleTranscribe}>
        ▶️ Transcribe (simulation)
      </button>

      {audioFiles.length > 0 && (
        <div className="file-list">
          <div className="file-list-header">
            <h3>Selected files:</h3>
            <button
              className="clear-files-button"
              onClick={() => setAudioFiles([])}
            >
              Clear
            </button>
          </div>

          <ul>
            {audioFiles.map((file, idx) => (
              <li key={idx}>{file.name}</li>
            ))}
          </ul>
        </div>
      )}

      {transcriptionResult && (
        <div className="result">
          <h3>Transcription:</h3>
          <p>{transcriptionResult}</p>
        </div>
      )}
    </div>
  );
}

export default SttPage;
