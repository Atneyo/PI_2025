import { useNavigate } from "react-router-dom";

function Header() {
  const navigate = useNavigate();

  return (
    <header className="app-header">
      <h1 className="app-title">AI Application</h1>
      
      <div className="header-buttons">
        <button onClick={() => navigate("/stt")}>
          Speach to Text
        </button>

        <button onClick={() => navigate("/video")}>
          Object Detection
        </button>
      </div>
    </header>
  );
}

export default Header;
