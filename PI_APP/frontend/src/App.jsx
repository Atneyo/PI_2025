import { useState } from "react";
import "./App.css";

function App() {
  const [model, setModel] = useState("whisper");
  const [audioFile, setAudioFile] = useState(null);
  const [textResult, setTextResult] = useState("");

  const handleFileChange = (e) => {
    setAudioFile(e.target.files[0]);
  };

  const handleTranscribe = () => {
    if (!audioFile) {
      alert("Sélectionne un fichier audio");
      return;
    }

    // Simulation pour l'instant
    setTextResult(
      `Résultat simulé pour le modèle "${model}" sur le fichier "${audioFile.name}"`
    );
  };

  return (
    <div className="container">
      <h1>🎤 Speech-to-Text Demo</h1>

      <label>Choisir un modèle</label>
      <select value={model} onChange={(e) => setModel(e.target.value)}>
        <option value="whisper">Whisper</option>
        <option value="vosk">Vosk</option>
        <option value="wav2vec2">Wav2Vec2</option>
      </select>

      <label>Choisir un fichier audio</label>
      <input type="file" accept="audio/*" onChange={handleFileChange} />

      <button onClick={handleTranscribe}>
        ▶️ Transcrire (simulation)
      </button>

      {textResult && (
        <div className="result">
          <h3>Transcription :</h3>
          <p>{textResult}</p>
        </div>
      )}
    </div>
  );
}

export default App;
