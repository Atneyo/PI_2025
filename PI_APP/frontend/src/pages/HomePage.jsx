import { useNavigate } from "react-router-dom";
import "./HomePage.css";

function HomePage() {
  const navigate = useNavigate();

  return (
    <div className="home-container">
      <h1>Welcome</h1>
      <div className="home-buttons">
        <button onClick={() => navigate("/video")}>Video</button>
        <button onClick={() => navigate("/stt")}>Speech-to-Text</button>
      </div>
    </div>
  );
}

export default HomePage;
