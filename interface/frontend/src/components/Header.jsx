import { useNavigate } from "react-router-dom";
import "./Header.css";

function Header() {
  const navigate = useNavigate();

  return (
    <header className="app-header">
      <h1 className="app-title" >My Application</h1>
      
      <div className="header-buttons">
        <button onClick={() => navigate("/stt")}>
          STT
        </button>

        <button onClick={() => navigate("/video")}>
          Video
        </button>
      </div>
    </header>
  );
}

export default Header;
