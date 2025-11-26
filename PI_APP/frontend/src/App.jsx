import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import HomePage from "./pages/HomePage";
import VideoPage from "./pages/VideoPage";
import SttPage from "./pages/SttPage";

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/video" element={<VideoPage />} />
        <Route path="/stt" element={<SttPage />} />
      </Routes>
    </Router>
  );
}

export default App;
