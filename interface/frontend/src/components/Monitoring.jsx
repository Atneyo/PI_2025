import React, { useEffect, useState } from "react";
import { getMonitoring } from "../api/api";

function Monitoring() {
  const [temperature, setTemperature] = useState(0);
  const [memoryUsed, setMemoryUsed] = useState(0);
  const [consumption, setConsumption] = useState(0);
  const [cpuUsage, setCpuUsage] = useState(0);
  const [hatUsage, setHatUsage] = useState("");

  
  useEffect(() => {
    // function to fetch data
    const fetchData = async () => {
      try {
        const data = await getMonitoring();
        // update all parameters
        setTemperature(data["temperature"]["cpu_temperature_c"] || 0);
        setMemoryUsed(data["memory"]["ram_percent_used"] || 0);
        setConsumption(data["swap"]["used_swap"] || 0);
        setCpuUsage(data["storage"]["used"] || 0);
        setHatUsage(data["energy"]["total_power_w"] || "");
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
          <p>Memory used: {memoryUsed} %</p>
          <p>Consumption: {consumption} W</p>
        </div>

        {/* Right column */}
        <div className="stats-column">
          <p>CPU : {cpuUsage}%</p>
          <p>HAT : {hatUsage}</p>
        </div>
      </div>
    </div>
  );
}

export default Monitoring;
