import React, { useState, useEffect } from "react";
import socService from "../../services/socService";
import "../dashboard/Dashboard.css";

const SocRiskAnalytics = () => {
  const [state, setState] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    socService.getSecurityState().then(setState).finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="dashboard-container">Loading Risk & ML Analytics...</div>;

  return (
    <div className="dashboard-container">
      <h1>Risk & ML Analytics</h1>
      <div className="dashboard-grid">
        <div className="dashboard-card">
          <h2>Isolation Forest</h2>
          <p>Anomaly Score: {state?.anomaly_score ?? "Not available"}</p>
        </div>
        <div className="dashboard-card">
          <h2>Random Forest</h2>
          <p>Risk Label: {state?.risk_label ?? "Not available"}</p>
          <p>RF High-Risk Probability: {state?.risk_score !== null && state?.risk_score !== undefined ? Number(state.risk_score * 100).toFixed(2) + "%" : "Not available"}</p>
        </div>
        <div className="dashboard-card">
          <h2>K-Means</h2>
          <p>Cluster ID: {state?.cluster_id ?? "Not available"}</p>
        </div>
      </div>
    </div>
  );
};
export default SocRiskAnalytics;
