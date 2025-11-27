import { useState, useRef } from "react";
import { useNavigate } from "react-router-dom";
import "./VideoPage.css";

function VideoPage() {
  const navigate = useNavigate();
  const [model, setModel] = useState("YOLOv11");
  const [videoFiles, setVideoFiles] = useState([]);
  const [videoResult, setVideoResult] = useState("");
  const [selectedVideoURL, setSelectedVideoURL] = useState(null);

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

    // ▶️ On prend la première vidéo pour l’afficher
    const videoURL = URL.createObjectURL(videoFiles[0]);
    setSelectedVideoURL(videoURL);

    const filenames = videoFiles.map(f => f.name).join(", ");
    setVideoResult(
      `Résultat simulé pour le modèle "${model}" sur les fichiers : ${filenames}`
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

      {/* --- ZONE DRAG & DROP --- */}
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
          accept="video/*"
          style={{ display: "none" }}
          onChange={handleFileChange}
        />
      </div>

      {/* --- SELECT MODEL --- */}
      <label>Choisir un modèle</label>
      <select value={model} onChange={(e) => setModel(e.target.value)}>
        <option value="YOLOv11">YOLO v11</option>
        <option value="YOLOv8">YOLO v8</option>
      </select>

      <button onClick={handleTranscribe}>▶️ Analyser (simulation)</button>

      {/* --- LISTE DES FICHIERS + BOUTON CLEAR --- */}
      {videoFiles.length > 0 && (
        <div className="file-list">
          <div className="file-list-header">
            <h3>Fichiers sélectionnés :</h3>
            <button
              className="clear-files-button"
              onClick={() => {
                setVideoFiles([]);
                setSelectedVideoURL(null);
                setVideoResult("");
              }}
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

      {/* --- LECTEUR VIDÉO --- */}
      {selectedVideoURL && (
        <div className="video-preview">
          <h3>Aperçu vidéo :</h3>
          <video
            src={selectedVideoURL}
            controls
            autoPlay
            width="600"
            style={{ borderRadius: "8px", marginTop: "10px" }}
          />
        </div>
      )}

      {/* --- RÉSULTAT --- */}
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
