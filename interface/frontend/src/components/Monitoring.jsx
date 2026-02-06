import React, { useEffect, useState } from "react";
import { getMonitoring } from "../api/api";

function Monitoring() {
  const [temperature, setTemperature] = useState(0);
  const [memoryUsed, setMemoryUsed] = useState(0);
  const [consumption, setConsumption] = useState(0);
  const [isHat, setIsHat] = useState(false);
  const [isCamera, setIsCamera] = useState(false);

  
  useEffect(() => {
    // function to fetch data
    const fetchData = async () => {
      try {
        const data = await getMonitoring();
        // update all parameters
        setTemperature(data["temperature"]["cpu_temperature_c"] || 0);
        setMemoryUsed(data["memory"]["ram_percent_used"] || 0);
        setConsumption(data["energy"]["total_power_w"] || 0);
        setIsHat(data["hailo_presence"] || false);
        setIsCamera(data["cameras"]["Rpi_cameras"] || data["cameras"]["Usb_cameras"] || false);
      } catch (err) {
        console.error("Error during monitoring fetch:", err);
      }
    };

    // initial fetch
    fetchData();

    // fetch all 10 seconds
    const interval = setInterval(fetchData, 10000); // delay in milliseconds

    // cleanup when component destructed
    return () => clearInterval(interval);
  }, []);


  return (
    <div>
      <h2>Monitoring</h2>
      <div className="stats-row">
        {/* Left column */}
        <div className="stats-column">
          <p>Temperature: {temperature}°C</p>
          <p>Memory used (RAM): {memoryUsed} %</p>
          <p>Consumption: {consumption} W</p>
        </div>

        {/* Right column */}
        <div className="stats-column">
          {/* Ligne pour le HAT */}
          <div className="status-item">
            <span className={`led-indicator ${isHat ? "on" : "off"}`}></span>
            <span>HAT</span>
          </div>

          {/* Ligne pour la Caméra */}
          <div className="status-item">
            <span className={`led-indicator ${isCamera ? "on" : "off"}`}></span>
            <span>Camera</span>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Monitoring;
