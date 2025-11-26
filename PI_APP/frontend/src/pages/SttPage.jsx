import { useState, useRef } from "react";
import { useNavigate } from "react-router-dom"; // ← import
import "./SttPage.css";


function SttPage() {
  const navigate = useNavigate();
  const [model, setModel] = useState("whisper");
  const [audioFiles, setAudioFiles] = useState([]);
  const [textResult, setTextResult] = useState("");

  const fileInputRef = useRef(null);

  const handleFiles = (files) => {
    const fileArray = Array.from(files).filter(file =>
      file.type.startsWith("audio/")
    );
    setAudioFiles((prev) => [...prev, ...fileArray]);
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
      alert("Sélectionne un fichier audio");
      return;
    }

    // Simulation pour l'instant
    const filenames = audioFiles.map(f => f.name).join(", ");
    setTextResult(
      `Résultat simulé pour le modèle "${model}" sur les fichiers : ${filenames}`
    );
  };

  return (
    <div className="container">
  <header className="app-header">
    <h1>Speech-to-Text Demo</h1>
    <button
      className="video-button"
      onClick={() => navigate("/video")} // ← redirige vers /video
    >
      Vidéo
    </button>

  </header>

  {/* Zone Drag & Drop */}
  <div
    className="drop-zone"
    onDrop={handleDrop}
    onDragOver={handleDragOver}
  >
    <p>Glisser-déposer des fichiers audio ici</p>
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
    <option value="whisper">Whisper</option>
    <option value="vosk">Vosk</option>
    <option value="wav2vec2">Wav2Vec2</option>
  </select>

  <button onClick={handleTranscribe}>
    ▶️ Transcrire (simulation)
  </button>

  {audioFiles.length > 0 && (
    <div className="file-list">
      <h3>Fichiers sélectionnés :</h3>
      <ul>
        {audioFiles.map((file, idx) => (
          <li key={idx}>{file.name}</li>
        ))}
      </ul>
    </div>
  )}

  {textResult && (
    <div className="result">
      <h3>Transcription :</h3>
      <p>{textResult}</p>
    </div>
  )}
</div>


  );
}

export default SttPage;
