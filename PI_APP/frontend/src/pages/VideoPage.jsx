import { useState, useRef } from "react";
import { useNavigate } from "react-router-dom";
import "./VideoPage.css";

function VideoPage() {
  const navigate = useNavigate();
  const [model, setModel] = useState("YOLOv11");
  const [videoFiles, setVideoFiles] = useState([]);
  const [analysisResult, setAnalysisResult] = useState("");
  const [selectedVideoURL, setSelectedVideoURL] = useState(null);

  const fileInputRef = useRef(null);

  const handleFiles = (files) => {
    const filteredFiles = Array.from(files).filter(file =>
      file.type.startsWith("video/")
    );
    setVideoFiles((prev) => [...prev, ...filteredFiles]);
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

  const handleAnalyze = () => {
    if (videoFiles.length === 0) {
      alert("Please select a video file");
      return;
    }

    // ▶️ Preview the first video
    const videoURL = URL.createObjectURL(videoFiles[0]);
    setSelectedVideoURL(videoURL);

    const filenames = videoFiles.map(f => f.name).join(", ");
    setAnalysisResult(
      `Simulated result for the model "${model}" on files: ${filenames}`
    );
  };

  return (
    <div className="container">
      {/* --- HEADER --- */}
      <header className="app-header">
        <h1>Video Demo</h1>
        <button className="stt-button" onClick={() => navigate("/stt")}>
          STT
        </button>
      </header>

      {/* --- DRAG & DROP ZONE --- */}
      <div
        className="drop-zone"
        onDrop={handleDrop}
        onDragOver={handleDragOver}
      >
        <p>Drag and drop video files here</p>
        <button onClick={handleAddFolder}>Add Folder</button>
        <input
          type="file"
          ref={fileInputRef}
          webkitdirectory="true"
          directory=""
          multiple
          accept="video/*"
          style={{ display: "none" }}
          onChange={handleFileChange}
        />
      </div>

      {/* --- SELECT MODEL --- */}
      <label>Select a model</label>
      <select value={model} onChange={(e) => setModel(e.target.value)}>
        <option value="YOLOv11">YOLO v11</option>
        <option value="YOLOv8">YOLO v8</option>
      </select>

      <button onClick={handleAnalyze}>▶️ Analyze (simulation)</button>

      {/* --- FILE LIST + CLEAR BUTTON --- */}
      {videoFiles.length > 0 && (
        <div className="file-list">
          <div className="file-list-header">
            <h3>Selected files:</h3>
            <button
              className="clear-files-button"
              onClick={() => {
                setVideoFiles([]);
                setSelectedVideoURL(null);
                setAnalysisResult("");
              }}
            >
              Clear
            </button>
          </div>

          <ul>
            {videoFiles.map((file, idx) => (
              <li key={idx}>{file.name}</li>
            ))}
          </ul>
        </div>
      )}

      {/* --- VIDEO PREVIEW --- */}
      {selectedVideoURL && (
        <div className="video-preview">
          <h3>Video Preview:</h3>
          <video
            src={selectedVideoURL}
            controls
            autoPlay
            width="600"
            style={{ borderRadius: "8px", marginTop: "10px" }}
          />
        </div>
      )}

      {/* --- RESULT --- */}
      {analysisResult && (
        <div className="result">
          <h3>Analysis:</h3>
          <p>{analysisResult}</p>
        </div>
      )}
    </div>
  );
}

export default VideoPage;
