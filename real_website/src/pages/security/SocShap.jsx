import React, { useState, useEffect } from "react";
import forensicsService from "../../services/forensicsService";
import "../dashboard/Dashboard.css";

const formatTimestamp = (timestamp) => {
  if (!timestamp) return 'N/A';
  const normalized = timestamp.endsWith('Z') ? timestamp : `${timestamp}Z`;
  const date = new Date(normalized);
  if (Number.isNaN(date.getTime())) return timestamp;
  return date.toLocaleString();
};

const FactorCard = ({ factor, type }) => {
  const isSupporting = type === 'supporting';
  const bgColor = isSupporting ? 'rgba(46, 125, 50, 0.1)' : 'rgba(198, 40, 40, 0.1)';
  const borderColor = isSupporting ? 'rgba(46, 125, 50, 0.3)' : 'rgba(198, 40, 40, 0.3)';
  const textColor = isSupporting ? '#4caf50' : '#f44336';
  const icon = isSupporting ? '✓' : '⚠';

  return (
    <div style={{
      backgroundColor: bgColor,
      border: `1px solid ${borderColor}`,
      borderRadius: '8px',
      padding: '12px 16px',
      marginBottom: '12px',
      display: 'flex',
      flexDirection: 'column',
      gap: '8px'
    }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <strong style={{ fontSize: '1rem', color: '#fff' }}>
          <span style={{ color: textColor, marginRight: '8px' }}>{icon}</span>
          {factor.display_name}
        </strong>
        <span style={{ 
          backgroundColor: borderColor, 
          color: textColor, 
          padding: '2px 8px', 
          borderRadius: '12px', 
          fontSize: '0.85rem',
          fontWeight: 'bold'
        }}>
          {factor.shap_value > 0 ? '+' : ''}{factor.shap_value.toFixed(4)}
        </span>
      </div>
      <div style={{ fontSize: '0.9rem', color: 'var(--text-secondary, #aaa)' }}>
        Value: <strong style={{ color: '#fff' }}>{factor.source_value}</strong>
      </div>
      <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary, #aaa)', fontStyle: 'italic' }}>
        {isSupporting ? 'Supports the prediction' : 'Pushes away from the prediction'}
      </div>
    </div>
  );
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
    <div className="dashboard-container" style={{ height: "auto", minHeight: "100%", paddingBottom: "2rem" }}>
      <h1 className="page-title">SHAP / XAI Explanations</h1>
      {shapData.length === 0 ? (
        <p style={{ color: 'var(--text-secondary, #aaa)' }}>No SHAP explanations available.</p>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: "30px" }}>
          {shapData.map((e) => {
            const shap = e.details.shap;
            const prediction = shap.prediction.toUpperCase();
            const probability = shap.model_probability ? (shap.model_probability * 100).toFixed(1) + '%' : 'N/A';
            const riskColor = prediction === 'HIGH' ? '#f44336' : prediction === 'MEDIUM' ? '#ff9800' : '#4caf50';

            return (
              <div key={e.evidence_id} className="dashboard-card" style={{ padding: "24px", display: "flex", flexDirection: "column", gap: "24px" }}>
                
                {/* Header Information */}
                <div>
                  <h3 style={{ margin: "0 0 8px 0", fontSize: "1.2rem", color: '#fff' }}>
                    Event ID: {e.details?.event?.event_id || e.evidence_id} | Type: {e.details?.event?.event_type || e.details?.event_type || e.event_type || "Unknown"}
                  </h3>
                  <div style={{ display: "flex", gap: "20px", color: 'var(--text-secondary, #aaa)', fontSize: '0.95rem' }}>
                    <span><strong>Time:</strong> {formatTimestamp(e.timestamp)}</span>
                    <span><strong>User:</strong> {e.user}</span>
                    <span><strong>Resource:</strong> {e.resource}</span>
                  </div>
                </div>

                {/* Summary Card */}
                <div style={{
                  backgroundColor: 'rgba(0, 255, 204, 0.05)',
                  border: '1px solid rgba(0, 255, 204, 0.2)',
                  borderRadius: '12px',
                  padding: '20px',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '12px'
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '16px', flexWrap: 'wrap' }}>
                    <div style={{ fontSize: '1.1rem', color: '#fff' }}>
                      Prediction: <strong style={{ color: riskColor, letterSpacing: '1px' }}>{prediction} RISK</strong>
                    </div>
                    {shap.model_probability && (
                      <div style={{ fontSize: '1.1rem', color: '#fff' }}>
                        Probability: <strong>{probability}</strong>
                      </div>
                    )}
                  </div>
                  
                  {shap.explanation_summary && (
                    <div style={{ fontSize: '1.05rem', color: '#fff', lineHeight: '1.5' }}>
                      {shap.explanation_summary}
                    </div>
                  )}
                  
                  <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary, #888)', marginTop: '8px' }}>
                    <em>Note: SHAP explains the Random Forest risk prediction. The final Zero Trust action may also depend on anomaly detection, authorization rules, privilege mismatch, and other security context.</em>
                  </div>
                </div>

                {/* Factors Grid */}
                <div style={{ 
                  display: 'grid', 
                  gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', 
                  gap: '24px' 
                }}>
                  {/* Supporting Factors */}
                  <div>
                    <h4 style={{ color: '#4caf50', marginBottom: '16px', fontSize: '1.1rem', borderBottom: '1px solid rgba(76, 175, 80, 0.2)', paddingBottom: '8px' }}>
                      Main Factors Supporting {prediction}
                    </h4>
                    {shap.supporting_factors && shap.supporting_factors.length > 0 ? (
                      shap.supporting_factors.map((f, i) => (
                        <FactorCard key={`supp-${i}`} factor={f} type="supporting" />
                      ))
                    ) : (
                      <p style={{ color: 'var(--text-secondary, #aaa)', fontSize: '0.9rem' }}>No significant supporting factors.</p>
                    )}
                  </div>

                  {/* Opposing Factors */}
                  <div>
                    <h4 style={{ color: '#f44336', marginBottom: '16px', fontSize: '1.1rem', borderBottom: '1px solid rgba(244, 67, 54, 0.2)', paddingBottom: '8px' }}>
                      Main Factors Opposing {prediction}
                    </h4>
                    {shap.opposing_factors && shap.opposing_factors.length > 0 ? (
                      shap.opposing_factors.map((f, i) => (
                        <FactorCard key={`opp-${i}`} factor={f} type="opposing" />
                      ))
                    ) : (
                      <p style={{ color: 'var(--text-secondary, #aaa)', fontSize: '0.9rem' }}>No significant opposing factors.</p>
                    )}
                  </div>
                </div>

                {/* Collapsible Detailed Table */}
                <details style={{ 
                  backgroundColor: 'rgba(255, 255, 255, 0.02)',
                  border: '1px solid rgba(255, 255, 255, 0.1)',
                  borderRadius: '8px',
                  padding: '16px',
                  marginTop: '12px'
                }}>
                  <summary style={{ 
                    cursor: 'pointer', 
                    color: 'var(--text-secondary, #aaa)',
                    fontSize: '1rem',
                    fontWeight: '600',
                    outline: 'none',
                    userSelect: 'none'
                  }}>
                    View Detailed SHAP Contributions
                  </summary>
                  
                  <div style={{ marginTop: '20px' }}>
                    <div style={{ display: 'flex', gap: '20px', marginBottom: '16px', color: '#fff', fontSize: '0.95rem' }}>
                      <span><strong>Explained Class:</strong> {prediction}</span>
                      <span><strong>Base Value:</strong> {shap.explanation.base_value !== undefined ? shap.explanation.base_value.toFixed(4) : "N/A"}</span>
                    </div>

                    {shap.explanation.contributions.length > 0 ? (
                      <div style={{ overflowX: 'auto' }}>
                        <table className="data-table">
                          <thead>
                            <tr>
                              <th>Feature Name</th>
                              <th>Contribution Value</th>
                              <th>Effect</th>
                            </tr>
                          </thead>
                          <tbody>
                            {shap.explanation.contributions.map((c, i) => {
                              const effectColor = c.contribution > 0 ? '#4caf50' : c.contribution < 0 ? '#f44336' : 'var(--text-secondary, #aaa)';
                              return (
                                <tr key={i}>
                                  <td style={{ color: '#fff' }}>{c.feature_name}</td>
                                  <td style={{ color: '#fff' }}>{c.contribution.toFixed(4)}</td>
                                  <td>
                                    <span style={{
                                      backgroundColor: c.contribution > 0 ? 'rgba(76, 175, 80, 0.1)' : c.contribution < 0 ? 'rgba(244, 67, 54, 0.1)' : 'rgba(255, 255, 255, 0.1)',
                                      color: effectColor,
                                      padding: '4px 10px',
                                      borderRadius: '12px',
                                      fontSize: '0.85rem',
                                      fontWeight: '600'
                                    }}>
                                      {c.contribution > 0 ? `Supports ${prediction}` : c.contribution < 0 ? `Opposes ${prediction}` : "Neutral"}
                                    </span>
                                  </td>
                                </tr>
                              );
                            })}
                          </tbody>
                        </table>
                      </div>
                    ) : (
                      <p style={{ color: 'var(--text-secondary, #aaa)' }}>No feature contributions available.</p>
                    )}
                  </div>
                </details>

              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default SocShap;
