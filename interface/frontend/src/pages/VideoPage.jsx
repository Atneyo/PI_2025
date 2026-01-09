import { useState, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { analyzeVideo } from "../api/api";
import Parameters from "../components/Parameters";
import Monitoring from "../components/Monitoring";
import Statistics from "../components/Statistics";
import Header from "../components/Header";

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

  const handleAnalyze = async () => {
    if (videoFiles.length === 0) {
      alert("Please select a video file");
      return;
    }

    // Print result video
    try {
      const data = await analyzeVideo(videoFiles); // call backend (see api.jsx)
      setSelectedVideoURL(data["video"]);
    } catch (err) {
      console.error("Error during analyze :",err);
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
            <h1 className="app-title" >Object detection</h1>
            {/* Drag & Drop Zone */}
            <div
              className="drop-zone"
              onDrop={handleDrop}
              onDragOver={handleDragOver}
            >
              <p>Drag and drop video files here</p>
              <button onClick={handleAddFolder}>Add Files</button>
              <input
                type="file"
                ref={fileInputRef}
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

            <button onClick={handleAnalyze}>▶️ Analyze</button>

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

export default VideoPage;
