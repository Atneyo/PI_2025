import { useNavigate } from "react-router-dom";


function HomePage() {
  const navigate = useNavigate();

  return (
    <div className="home-container">
      <h1 className="app-title">AI Application</h1>
      <p>This application allows you to transcribe audio into text and detect objects in videos.</p>
      <p>Using AI models, the object detection feature identifies and extracts all objects present in your selected video, while the speech-to-text feature generates transcriptions from any audio or video file you choose.</p>
      <div className="home-buttons">
        <button onClick={() => navigate("/video")}>Object Detection</button>
        <button onClick={() => navigate("/stt")}>Speech to Text</button>
      </div>
    </div>
  );
}

export default HomePage;
