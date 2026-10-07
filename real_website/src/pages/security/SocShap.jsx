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
              
              <hr style={{ margin: "15px 0", borderTop: "1px solid #ddd" }} />
              <h4>WHY WAS THIS PREDICTION MADE?</h4>
              
              <div style={{ marginBottom: "15px", padding: "15px", backgroundColor: "#f9f9f9", borderRadius: "5px", borderLeft: "4px solid #0056b3" }}>
                <p><strong>Random Forest Prediction:</strong> <span style={{ textTransform: "uppercase", fontWeight: "bold" }}>{e.details.shap.prediction}</span></p>
                {e.details.shap.model_probability && <p><strong>Probability:</strong> {(e.details.shap.model_probability * 100).toFixed(1)}%</p>}
                
                {e.details.shap.explanation_summary && (
                  <p style={{ marginTop: "10px", fontStyle: "italic", color: "#444" }}>
                    "{e.details.shap.explanation_summary}"
                  </p>
                )}
                
                <p style={{ marginTop: "10px", fontSize: "13px", color: "#666" }}>
                  <em>Note: SHAP explains the Random Forest risk prediction. The final Zero Trust action may also depend on anomaly detection, authorization rules, privilege mismatch, and other security context.</em>
                </p>
              </div>

              {e.details.shap.supporting_factors && e.details.shap.supporting_factors.length > 0 && (
                <div style={{ marginBottom: "15px" }}>
                  <h5 style={{ color: "#2E7D32", margin: "10px 0 5px 0" }}>Main factors supporting {e.details.shap.prediction.toUpperCase()}:</h5>
                  <ul style={{ listStyleType: "none", paddingLeft: "0" }}>
                    {e.details.shap.supporting_factors.map((f, i) => (
                      <li key={i} style={{ marginBottom: "10px", padding: "10px", border: "1px solid #e0e0e0", borderRadius: "4px", backgroundColor: "#f4fff4" }}>
                        <strong style={{ fontSize: "15px" }}>✓ {f.display_name}</strong>
                        <div style={{ marginLeft: "20px", fontSize: "14px", marginTop: "5px" }}>
                          <div>Value: <strong>{f.source_value}</strong></div>
                          <div>Impact: <span style={{ color: "#2E7D32", fontWeight: "bold" }}>+{f.shap_value.toFixed(4)}</span></div>
                          <div style={{ color: "#555", fontSize: "13px", marginTop: "4px" }}>Supports the {e.details.shap.prediction}-risk prediction.</div>
                        </div>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {e.details.shap.opposing_factors && e.details.shap.opposing_factors.length > 0 && (
                <div style={{ marginBottom: "20px" }}>
                  <h5 style={{ color: "#C62828", margin: "10px 0 5px 0" }}>Main factors opposing {e.details.shap.prediction.toUpperCase()}:</h5>
                  <ul style={{ listStyleType: "none", paddingLeft: "0" }}>
                    {e.details.shap.opposing_factors.map((f, i) => (
                      <li key={i} style={{ marginBottom: "10px", padding: "10px", border: "1px solid #e0e0e0", borderRadius: "4px", backgroundColor: "#fff4f4" }}>
                        <strong style={{ fontSize: "15px" }}>⚠ {f.display_name}</strong>
                        <div style={{ marginLeft: "22px", fontSize: "14px", marginTop: "5px" }}>
                          <div>Value: <strong>{f.source_value}</strong></div>
                          <div>Impact: <span style={{ color: "#C62828", fontWeight: "bold" }}>{f.shap_value.toFixed(4)}</span></div>
                          <div style={{ color: "#555", fontSize: "13px", marginTop: "4px" }}>Pushes the prediction away from {e.details.shap.prediction} risk.</div>
                        </div>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              <hr style={{ margin: "20px 0", borderTop: "1px dashed #ccc" }} />
              <h4>Detailed SHAP Contributions</h4>
              <p><strong>Explained Class:</strong> <span style={{ textTransform: "capitalize" }}>{e.details.shap.prediction}</span></p>
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
                        <td style={{padding: "8px", color: c.contribution > 0 ? "#2E7D32" : "#C62828", fontWeight: "500"}}>
                          {c.contribution > 0 ? `Supports ${e.details.shap.prediction}` : c.contribution < 0 ? `Opposes ${e.details.shap.prediction}` : "Neutral"}
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
