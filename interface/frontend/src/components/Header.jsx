import { useNavigate } from "react-router-dom";

function Header() {
  const navigate = useNavigate();

  return (
    <header className="app-header">
      <h1 className="app-title"><button className="title-button" onClick={() => navigate("/")}>AI Application</button></h1>
      
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
