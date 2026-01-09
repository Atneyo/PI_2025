function Monitoring() {
  const temperature = 0;
  const memoryUsed = 0;
  const consumption = 0;
  const cpuUsage = 0;
  const hatUsage = 0;

  return (
    <div>
      <h2>Monitoring</h2>
      <div className="stats-row">
        {/* Left column */}
        <div className="column">
          <p>Temperature: {temperature}°C</p>
          <p>Memory used: {memoryUsed} MB</p>
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
