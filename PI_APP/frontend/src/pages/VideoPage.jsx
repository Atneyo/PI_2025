import { useState, useRef } from "react";
import { useNavigate } from "react-router-dom";
import "./VideoPage.css";


function VideoPage() {
  const navigate = useNavigate();
  const [model, setModel] = useState("YOLOv11");
  const [videoFiles, setVideoFiles] = useState([]);
  const [videoResult, setVideoResult] = useState("");

  const fileInputRef = useRef(null);

  const handleFiles = (files) => {
    const fileArray = Array.from(files).filter(file =>
      file.type.startsWith("video/")
    );
    setVideoFiles((prev) => [...prev, ...fileArray]);
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
    if (videoFiles.length === 0) {
      alert("Sélectionne un fichier vidéo");
      return;
    }

    // Simulation pour l'instant
    const filenames = videoFiles.map(f => f.name).join(", ");
    setVideoResult(
      `Résultat simulé pour le modèle "${model}" sur les fichiers : ${filenames}`
    );
  };

  return (
    <div className="container">
  <header className="app-header">
    <h1>Video Demo</h1>
    <button
      className="stt-button"
      onClick={() => navigate("/stt")} // ← redirect to /stt
    >
      STT
    </button>

  </header>

  {/* Zone Drag & Drop */}
  <div
    className="drop-zone"
    onDrop={handleDrop}
    onDragOver={handleDragOver}
  >
    <p>Glisser-déposer des fichiers vidéos ici</p>
    <button onClick={handleAddFolder}>Ajouter un dossier</button>
    <input
      type="file"
      ref={fileInputRef}
      webkitdirectory="true"
      directory=""
      multiple
      style={{ display: "none" }}
      onChange={handleFileChange}
    />
  </div>

  <label>Choisir un modèle</label>
  <select value={model} onChange={(e) => setModel(e.target.value)}>
    <option value="YOLOv11">YOLO v11</option>
    <option value="YOLOv8">YOLO v8</option>
  </select>

  <button onClick={handleTranscribe}>
    ▶️ Analyser (simulation)
  </button>

  {videoFiles.length > 0 && (
    <div className="file-list">
      <div className="file-list-header">
        <h3>Fichiers sélectionnés :</h3>
        <button
          className="clear-files-button"
          onClick={() => setVideoFiles([])}
        >
          Vider
        </button>
      </div>
    
      <ul>
        {videoFiles.map((file, idx) => (
          <li key={idx}>{file.name}</li>
        ))}
      </ul>
    </div>
  )}

  {videoResult && (
    <div className="result">
      <h3>Analyse :</h3>
      <p>{videoResult}</p>
    </div>
  )}
</div>


  );
}

export default VideoPage;
