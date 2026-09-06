import React, { useState, useEffect } from "react";
import forensicsService from "../../services/forensicsService";
import "../dashboard/Dashboard.css";

const formatTimestamp = (timestamp) => {
  if (!timestamp) return 'N/A';

  const normalized = timestamp.endsWith('Z')
    ? timestamp
    : `${timestamp}Z`;

  const date = new Date(normalized);

  if (Number.isNaN(date.getTime())) return timestamp;

  return date.toLocaleString();
};

const SocShap = () => {
  const [evidence, setEvidence] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    forensicsService.getEvidence().then(setEvidence).finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="dashboard-container">Loading SHAP Explanations...</div>;

  const shapData = evidence
    .filter(e => e.details?.shap && e.details.shap.explanation && Array.isArray(e.details.shap.explanation.contributions))
    .sort((a, b) => b.evidence_id - a.evidence_id);

  return (
    <div className="dashboard-container" style={{ height: "auto", minHeight: "100%" }}>
      <h1>SHAP / XAI Explanations</h1>
      {shapData.length === 0 ? <p>No SHAP explanations available.</p> : (
        <div style={{display:"flex", flexDirection:"column", gap:"20px"}}>
          {shapData.map(e => (
            <div key={e.evidence_id} className="dashboard-card">
              <h3>Event ID: {e.details?.event?.event_id || e.evidence_id} | Type: {e.details?.event?.event_type || e.details?.event_type || e.event_type || "Unknown"}</h3>
              <p><strong>Timestamp:</strong> {formatTimestamp(e.timestamp)}</p>
              <p><strong>User:</strong> {e.user}</p>
              <p><strong>Resource:</strong> {e.resource}</p>
              <p><strong>RF Prediction:</strong> {e.details.shap.prediction}</p>
              <p><strong>SHAP Base Value:</strong> {e.details.shap.explanation.base_value !== undefined ? e.details.shap.explanation.base_value.toFixed(4) : "N/A"}</p>
              
              <h4>SHAP Contributions</h4>
              {e.details.shap.explanation.contributions.length > 0 ? (
                <table className="shap-table" style={{width: "100%", textAlign: "left", borderCollapse: "collapse"}}>
                  <thead>
                    <tr style={{borderBottom: "1px solid #ddd"}}>
                      <th style={{padding: "8px"}}>Feature Name</th>
                      <th style={{padding: "8px"}}>Contribution Value</th>
                      <th style={{padding: "8px"}}>Effect</th>
                    </tr>
                  </thead>
                  <tbody>
                    {e.details.shap.explanation.contributions.map((c, i) => (
                      <tr key={i} style={{borderBottom: "1px solid #eee"}}>
                        <td style={{padding: "8px"}}>{c.feature_name}</td>
                        <td style={{padding: "8px"}}>{c.contribution.toFixed(4)}</td>
                        <td style={{padding: "8px", color: c.contribution > 0 ? "red" : "green"}}>
                          {c.contribution > 0 ? "Positive (Increases Risk)" : c.contribution < 0 ? "Negative (Decreases Risk)" : "Neutral"}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              ) : (
                <p>No feature contributions.</p>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
export default SocShap;
