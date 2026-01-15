import { useState, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { analyzeAudio } from "../api/api";
import Parameters from "../components/Parameters";
import Monitoring from "../components/Monitoring";
import Statistics from "../components/Statistics";
import Header from "../components/Header";

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

  const handleTranscribe = async () => {
    if (audioFiles.length === 0) {
      alert("Please select an audio file");
      return;
    }

    // print transcription
    try {
      const data = await analyzeAudio(audioFiles); // call backend (see api.jsx)
      setTranscriptionResult(data["text"]);
    } catch (err) {
      console.error("Error during transcription :",err);
    }

  };

  return (
    <div>
      <div className="header">
          <Header/>
      </div>

      <div className="page-layout">

        {/* Left part */}
        <div className="left-panel">
          <div className="container">
            <h1 className="app-title" >Speech to Text</h1>
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
              <option value="whisper">Whisper Base</option>
            </select>

            <button onClick={handleTranscribe}>
              ▶️ Transcribe
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
        </div>

        {/* Right part */}
        <div className="right-panel">
          <Parameters />
          <Monitoring/>
          <Statistics/>
        </div>
      </div>
    </div>
  );
}

export default SttPage;
