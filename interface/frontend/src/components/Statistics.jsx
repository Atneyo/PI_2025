function Statistics() {
  const fps = 0;
  return (
    <div>
      <h2>Statistics</h2>
      <div className="stats-row">
        {/* Left column */}
        <div className="stats-column">
          <p>Treatment: {fps} fps</p>
        </div>
      </div>
    </div>
  );
}

export default Statistics;
