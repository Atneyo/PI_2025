import React, { useState, useEffect } from "react";

function Parameters({ settingsRef, showFps = true }) {

  const [isOnHat, setIsOnHat] = useState(false);
  const [isOnCam, setIsOnCam] = useState(false);
  const [selectedCamera, setSelectedCamera] = useState("");
  const [fps, setFps] = useState(15);

  useEffect(() => {
    if (settingsRef) {
      settingsRef.current = {
        isOnHat,
        fps,
        isOnCam,
        selectedCamera
      };
    }
  }, [isOnHat, isOnCam, selectedCamera, fps, settingsRef]);

  const handleChangeFps = (e) => {
    const value = e.target.value;
    // Accepter que le champ soit vide, sinon convertir en entier
    if (value === "") {
      setFps("");
    } else {
      const intValue = parseInt(value, 10);
      if (!isNaN(intValue)) {
        setFps(intValue);
      }
    }
  };

  return (
    <div>
      <h2>Parameters</h2>
      <div className="stats-row">
        {/* Left column */}
        <div className="stats-column">
          {/* HAT button */}
          <div className="control-item ">
            <label className="switch">
              <input type="checkbox" checked={isOnHat} onChange={() => setIsOnHat(!isOnHat)} />
              <span className="slider"></span>
            </label>
            <label>HAT</label>
          </div>
          {/* Enter FPS */}
          {showFps && (
          <div className="control-item">
            <input
              type="number"
              value={fps}
              onChange={handleChangeFps}
              className="number-input"
            />
            <label>FPS</label>
          </div>
          )}
        </div>

        {/* Right column */}
        {/* <div className="stats-column">
          <div className="control-item">
            <label className="switch">
              <input type="checkbox" checked={isOnCam} onChange={() => setIsOnCam(!isOnCam)} />
              <span className="slider"></span>
            </label>
            <label>Live</label>
          </div>
          <div className="control-item">
            <select
              value={selectedCamera}
              onChange={(e) => setSelectedCamera(e.target.value)}
            >
              <option value="">Select...</option>
              <option value="option1">Option 1</option>
              <option value="option2">Option 2</option>
              <option value="option3">Option 3</option>
            </select>
            <label>Camera:</label>
          </div>
        </div> */}
      </div>
    </div>
  );
}

export default Parameters;
