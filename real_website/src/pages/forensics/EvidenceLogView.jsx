import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import forensicsService from '../../services/forensicsService';
import { formatDateIST } from '../../utils/dateUtils';
import './Forensics.css';

function getPolicyRisk(action) {
    switch (action) {
        case 'Allow':
        case 'Access':
            return 'Low';
        case 'OTP':
        case 'Restrict':
            return 'Medium';
        case 'Block':
            return 'High';
        default:
            return 'Unknown';
    }
}

const EvidenceLogView = () => {
  const [evidence, setEvidence] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [verifyStatus, setVerifyStatus] = useState(null);
  const [verifying, setVerifying] = useState(false);
  const [selectedLog, setSelectedLog] = useState(null);
  const navigate = useNavigate();

  const getTriggers = (reason) => {
    if (!reason) return ["None — normal authorized access"];
    const triggers = [];
    if (reason.includes('privilege_mismatch')) triggers.push('Privilege Mismatch');
    if (reason.includes('rf_high_risk')) triggers.push('High Random Forest Risk');
    if (reason.includes('rf_medium_risk')) triggers.push('Medium Random Forest Risk');
    if (reason.includes('isolation_forest_anomaly')) triggers.push('Isolation Forest Anomaly');
    if (reason.includes('elevated_behavior')) triggers.push('Elevated K-Means Behaviour');
    
    if (triggers.length === 0) return ["None — normal authorized access"];
    return triggers;
  };

  const getHashVerificationStatus = (log, vStatus) => {
    if (!vStatus) return 'N/A';
    if (vStatus.status === 'VALID') return 'Verified / VALID';
    if (vStatus.status === 'TAMPER DETECTED') {
      if (vStatus.affected_id && log.evidence_id >= vStatus.affected_id) {
        return 'Invalid';
      }
      return 'Verified / VALID';
    }
    return 'Invalid';
  };

  useEffect(() => {
    fetchEvidence();
  }, []);

  const fetchEvidence = async () => {
    try {
      const data = await forensicsService.getEvidence();
      setEvidence(data);
    } catch (err) {
      if (err.response?.status === 403) {
        setError('Forbidden: Admin access required.');
      } else {
        setError(err.response?.data?.error || 'Failed to fetch evidence log');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleVerify = async () => {
    setVerifying(true);
    setVerifyStatus(null);
    try {
      const data = await forensicsService.verifyIntegrity();
      setVerifyStatus(data);
    } catch (err) {
      setVerifyStatus({ status: 'ERROR', reason: 'Verification request failed' });
    } finally {
      setVerifying(false);
    }
  };

  if (loading) return <div className="forensics-container">Loading evidence log...</div>;
  if (error) return <div className="forensics-container" style={{ color: 'red' }}>Error: {error}</div>;

  return (
    <div className="forensics-container">
      <div className="forensics-header">
        <button className="forensics-btn" onClick={() => navigate('/forensics')} style={{ float: 'right' }}>Back</button>
        <h1>Evidence Log</h1>
      </div>

      <button className="forensics-btn primary" onClick={handleVerify} disabled={verifying}>
        {verifying ? 'Verifying...' : 'Verify Evidence Integrity'}
      </button>

      {verifyStatus && (
        <div className={`status-banner ${verifyStatus.status === 'VALID' ? 'valid' : 'invalid'}`}>
          Evidence Integrity: {verifyStatus.status}
          {verifyStatus.reason && <p style={{ margin: '5px 0 0 0', fontWeight: 'normal' }}>{verifyStatus.reason}</p>}
        </div>
      )}

      {evidence.length === 0 ? (
        <p>No evidence logs found.</p>
      ) : (
        <div style={{ overflowX: 'auto', marginTop: '20px' }}>
          <table className="forensics-table">
            <thead>
              <tr>
                <th>Evidence ID</th>
                <th>Event ID</th>
                <th>Event Type</th>
                <th>Login Event ID</th>
                <th>Session ID</th>
                <th>Timestamp</th>
                <th>User</th>
                <th>Resource</th>
                <th>Policy Risk</th>
                <th>Policy Decision</th>
                <th>Record Hash</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {evidence.map(log => (
                <tr key={log.evidence_id}>
                  <td>{log.evidence_id}</td>
                  <td>{log.event_id || 'Not available'}</td>
                  <td>{log.event_type}</td>
                  <td>{log.login_event_id || 'Not available'}</td>
                  <td style={{ fontFamily: 'monospace' }}>{log.session_id ? log.session_id.substring(0,8) + '...' : 'Not available'}</td>
                  <td>{log.timestamp ? formatDateIST(log.timestamp) : 'Not available'}</td>
                  <td>{log.user || 'Not available'}</td>
                  <td>{log.resource || 'Not available'}</td>
                  <td>{getPolicyRisk(log.policy_decision)}</td>
                  <td>{log.policy_decision || 'Not available'}</td>
                  <td style={{ fontFamily: 'monospace', fontSize: '0.85em' }}>
                    {log.record_hash ? log.record_hash.substring(0, 16) + '...' : 'Not available'}
                  </td>
                  <td>
                    <button className="forensics-btn" onClick={() => setSelectedLog(log)}>Details</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {selectedLog && (
        <div className="evidence-modal-overlay" onClick={() => setSelectedLog(null)}>
          <div className="evidence-modal" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h2>Evidence Detail: {selectedLog.evidence_id}</h2>
              <button onClick={() => setSelectedLog(null)} className="close-btn">×</button>
            </div>
            
            <div className="modal-body">
              <div className="detail-section">
                <h3>EVENT</h3>
                <p><strong>Evidence ID:</strong> {selectedLog.evidence_id}</p>
                <p><strong>Event ID:</strong> {selectedLog.event_id || 'N/A'}</p>
                <p><strong>Event Type:</strong> {selectedLog.event_type}</p>
                <p><strong>Timestamp:</strong> {selectedLog.timestamp ? formatDateIST(selectedLog.timestamp) : 'N/A'}</p>
              </div>

              <div className="detail-section">
                <h3>SESSION</h3>
                <p><strong>Session ID:</strong> {selectedLog.session_id || 'N/A'}</p>
                <p><strong>Login Event ID:</strong> {selectedLog.login_event_id || 'N/A'}</p>
              </div>

              <div className="detail-section">
                <h3>USER</h3>
                <p><strong>User ID:</strong> {selectedLog.details?.user?.user_id || selectedLog.details?.user_id || 'N/A'}</p>
                <p><strong>Username:</strong> {selectedLog.user || 'N/A'}</p>
                <p><strong>Role:</strong> {selectedLog.details?.user?.role || 'N/A'}</p>
              </div>

              <div className="detail-section">
                <h3>ACCESS</h3>
                <p><strong>Resource:</strong> {selectedLog.resource || 'N/A'}</p>
                <p><strong>Sensitivity:</strong> {selectedLog.details?.resource?.sensitivity || 'N/A'}</p>
                <p><strong>Request Count:</strong> {selectedLog.details?.access?.request_count ?? 'N/A'}</p>
                <p><strong>Unauthorized Access:</strong> {selectedLog.details?.security?.unauthorized_access_attempt !== undefined ? String(selectedLog.details?.security?.unauthorized_access_attempt) : (selectedLog.details?.access?.unauthorized_access !== undefined ? String(selectedLog.details?.access?.unauthorized_access) : 'N/A')}</p>
                <p><strong>Privilege Mismatch:</strong> {selectedLog.details?.security?.privilege_mismatch !== undefined ? String(selectedLog.details?.security?.privilege_mismatch) : 'N/A'}</p>
              </div>

              <div className="detail-section">
                <h3>NETWORK / DEVICE</h3>
                <p><strong>IP Address:</strong> {selectedLog.details?.network?.ip_address || selectedLog.details?.ip_address || 'N/A'}</p>
                <p><strong>Device ID:</strong> {selectedLog.details?.device?.device_id || selectedLog.details?.device?.device_info || selectedLog.details?.device_info || 'N/A'}</p>
                <p><strong>Device Fingerprint:</strong> {selectedLog.details?.device?.device_fingerprint || 'N/A'}</p>
                <p><strong>IP Changed:</strong> {selectedLog.details?.network?.ip_changed_during_session !== undefined ? String(selectedLog.details?.network?.ip_changed_during_session) : 'N/A'}</p>
                <p><strong>Device Changed:</strong> {selectedLog.details?.device?.device_changed_during_session !== undefined ? String(selectedLog.details?.device?.device_changed_during_session) : 'N/A'}</p>
              </div>

              <div className="detail-section">
                <h3>ZERO TRUST DECISION</h3>
                <p><strong>Policy Decision:</strong> {selectedLog.policy_decision || 'N/A'}</p>
                {selectedLog.event_type === 'SessionTermination' ? (
                  <React.Fragment>
                    <p><strong>Action Taken:</strong> {selectedLog.action_taken || 'Session Terminated'}</p>
                    <p><strong>Session Outcome:</strong> {selectedLog.session_outcome || 'Terminated'}</p>
                    <p><strong>Termination Reason:</strong> {selectedLog.termination_reason || 'N/A'}</p>
                    <p><strong>Previous Session State:</strong> {selectedLog.details?.previous_session_state || 'Active'}</p>
                    <p><strong>Current Session State:</strong> {selectedLog.details?.current_session_state || 'Inactive'}</p>
                    <div style={{marginTop: '10px', padding: '10px', backgroundColor: '#fff3cd', color: '#856404', border: '1px solid #ffeeba', borderRadius: '4px'}}>
                      <strong>Explanation:</strong> {selectedLog.details?.explanation || 'Session terminated because the maximum number of OTP verification attempts was exceeded.'}
                    </div>
                  </React.Fragment>
                ) : (
                  <React.Fragment>
                    <p><strong>Action Taken:</strong> {selectedLog.policy_decision === 'Allow' ? 'Access Granted' : selectedLog.policy_decision === 'OTP' ? 'OTP Verification Required' : selectedLog.policy_decision === 'Restrict' ? 'Access Restricted' : selectedLog.policy_decision === 'Block' ? 'Access Blocked / Session Terminated' : 'N/A'}</p>
                    {(() => {
                      const triggers = getTriggers(selectedLog.details?.zero_trust?.reason);
                      return (
                        <div>
                          <strong>Trigger{triggers.length > 1 ? 's' : ''}: </strong>
                          {triggers.length === 1 ? triggers[0] : (
                            <ul style={{ margin: '5px 0 5px 20px' }}>
                              {triggers.map((t, i) => <li key={i}>{t}</li>)}
                            </ul>
                          )}
                          
                          {selectedLog.policy_decision === 'OTP' && triggers.includes('Isolation Forest Anomaly') && selectedLog.details?.ml?.random_forest?.risk_label === 'low' && (
                            <div style={{marginTop: '10px', padding: '10px', backgroundColor: '#fff3cd', color: '#856404', border: '1px solid #ffeeba', borderRadius: '4px'}}>
                              <strong>Explanation:</strong> Step-up authentication was required because an Isolation Forest anomaly was detected, despite the Random Forest model classifying the current event as low risk.
                            </div>
                          )}
                        </div>
                      );
                    })()}
                  </React.Fragment>
                )}
                <p style={{marginTop: '10px'}}><strong>HTTP Status:</strong> {selectedLog.details?.zero_trust?.http_status || 'N/A'}</p>
              </div>

              <div className="detail-section">
                <h3>ML RISK ASSESSMENT</h3>
                
                <div style={{marginBottom: '15px'}}>
                  <h4>Random Forest</h4>
                  <p><strong>Risk Label:</strong> {selectedLog.details?.ml?.random_forest?.risk_label === 'low' ? 'Low' : selectedLog.details?.ml?.random_forest?.risk_label === 'medium' ? 'Medium' : selectedLog.details?.ml?.random_forest?.risk_label === 'high' ? 'High' : (selectedLog.details?.ml?.random_forest?.risk_label || 'N/A')}</p>
                  <p><strong>High-Risk Probability:</strong> {selectedLog.details?.ml?.random_forest?.risk_score !== undefined && selectedLog.details?.ml?.random_forest?.risk_score !== null ? Number(selectedLog.details.ml.random_forest.risk_score * 100).toFixed(2) + '%' : 'N/A'}</p>
                </div>
                
                <div style={{marginBottom: '15px'}}>
                  <h4>Isolation Forest</h4>
                  <p><strong>Anomaly Status:</strong> {selectedLog.details?.ml?.isolation_forest?.is_anomaly !== undefined ? (selectedLog.details.ml.isolation_forest.is_anomaly ? 'Anomaly Detected' : 'Normal') : 'N/A'}</p>
                  <p><strong>Anomaly Score:</strong> {selectedLog.details?.ml?.isolation_forest?.anomaly_score !== undefined ? Number(selectedLog.details.ml.isolation_forest.anomaly_score).toFixed(2) : 'N/A'}</p>
                </div>
                
                <div>
                  <h4>K-Means</h4>
                  <p><strong>Cluster:</strong> {selectedLog.details?.ml?.kmeans?.cluster_id ?? 'N/A'}</p>
                  <p><strong>Behaviour:</strong> {selectedLog.details?.ml?.kmeans?.behavior_label || 'N/A'}</p>
                </div>
              </div>

              <div className="detail-section">
                <h3>SHAP ANALYSIS</h3>
                
                {selectedLog.details?.shap ? (() => {
                  const shap = selectedLog.details.shap;
                  const prediction = shap.prediction ? shap.prediction.toUpperCase() : 'N/A';
                  const probability = shap.model_probability ? (shap.model_probability * 100).toFixed(1) + '%' : 'N/A';
                  const riskColor = prediction === 'HIGH' ? '#f44336' : prediction === 'MEDIUM' ? '#ff9800' : '#4caf50';

                  return (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
                      <div style={{ padding: '16px', backgroundColor: 'rgba(0, 0, 0, 0.03)', borderRadius: '8px', borderLeft: `4px solid ${riskColor}` }}>
                        <p style={{ margin: '0 0 8px 0', fontSize: '1.05rem' }}>
                          <strong>Random Forest Prediction:</strong> <span style={{ color: riskColor, fontWeight: 'bold' }}>{prediction} RISK</span>
                        </p>
                        <p style={{ margin: '0 0 8px 0' }}><strong>Probability:</strong> {probability}</p>
                        <p style={{ margin: '0 0 8px 0' }}><strong>Explained Class:</strong> <span style={{ textTransform: 'capitalize' }}>{shap.prediction}</span></p>
                        <p style={{ margin: '0 0 8px 0' }}><strong>Base Value:</strong> {shap.explanation?.base_value !== undefined ? shap.explanation.base_value.toFixed(4) : 'N/A'}</p>
                      </div>

                      <div>
                        <h4 style={{ margin: '0 0 10px 0', fontSize: '1.1rem' }}>WHY WAS THIS PREDICTION MADE?</h4>
                        {shap.explanation_summary && (
                          <p style={{ fontStyle: 'italic', color: 'var(--text-secondary, #555)', marginBottom: '16px' }}>
                            "{shap.explanation_summary}"
                          </p>
                        )}
                        
                        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '20px' }}>
                          <div>
                            <h5 style={{ color: '#4caf50', margin: '0 0 10px 0', borderBottom: '1px solid rgba(76, 175, 80, 0.2)', paddingBottom: '4px' }}>Main factors supporting {prediction}</h5>
                            {shap.supporting_factors && shap.supporting_factors.length > 0 ? (
                              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                                {shap.supporting_factors.map((f, i) => (
                                  <div key={i} style={{ padding: '10px', backgroundColor: 'rgba(46, 125, 50, 0.05)', border: '1px solid rgba(46, 125, 50, 0.2)', borderRadius: '6px' }}>
                                    <div style={{ fontWeight: 'bold', color: '#333', marginBottom: '4px' }}><span style={{ color: '#4caf50', marginRight: '6px' }}>✓</span>{f.display_name}</div>
                                    <div style={{ fontSize: '0.9rem', color: '#555', marginLeft: '20px' }}>Value: <strong>{f.source_value}</strong></div>
                                    <div style={{ fontSize: '0.9rem', color: '#555', marginLeft: '20px' }}>SHAP Impact: <span style={{ color: '#4caf50', fontWeight: 'bold' }}>+{f.shap_value.toFixed(4)}</span></div>
                                    <div style={{ fontSize: '0.85rem', color: '#777', fontStyle: 'italic', marginLeft: '20px', marginTop: '4px' }}>Supports the {prediction}-risk prediction.</div>
                                  </div>
                                ))}
                              </div>
                            ) : <p style={{ color: '#777', fontSize: '0.9rem' }}>No significant supporting factors.</p>}
                          </div>

                          <div>
                            <h5 style={{ color: '#f44336', margin: '0 0 10px 0', borderBottom: '1px solid rgba(244, 67, 54, 0.2)', paddingBottom: '4px' }}>Main factors opposing {prediction}</h5>
                            {shap.opposing_factors && shap.opposing_factors.length > 0 ? (
                              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                                {shap.opposing_factors.map((f, i) => (
                                  <div key={i} style={{ padding: '10px', backgroundColor: 'rgba(198, 40, 40, 0.05)', border: '1px solid rgba(198, 40, 40, 0.2)', borderRadius: '6px' }}>
                                    <div style={{ fontWeight: 'bold', color: '#333', marginBottom: '4px' }}><span style={{ color: '#f44336', marginRight: '6px' }}>⚠</span>{f.display_name}</div>
                                    <div style={{ fontSize: '0.9rem', color: '#555', marginLeft: '22px' }}>Value: <strong>{f.source_value}</strong></div>
                                    <div style={{ fontSize: '0.9rem', color: '#555', marginLeft: '22px' }}>SHAP Impact: <span style={{ color: '#f44336', fontWeight: 'bold' }}>{f.shap_value.toFixed(4)}</span></div>
                                    <div style={{ fontSize: '0.85rem', color: '#777', fontStyle: 'italic', marginLeft: '22px', marginTop: '4px' }}>Pushes the prediction away from {prediction} risk.</div>
                                  </div>
                                ))}
                              </div>
                            ) : <p style={{ color: '#777', fontSize: '0.9rem' }}>No significant opposing factors.</p>}
                          </div>
                        </div>
                      </div>

                      <details style={{ marginTop: '10px', padding: '12px', backgroundColor: 'rgba(0,0,0,0.02)', border: '1px solid #e0e0e0', borderRadius: '6px' }}>
                        <summary style={{ fontWeight: 'bold', cursor: 'pointer', color: '#555' }}>Detailed SHAP Contributions</summary>
                        {shap.explanation && Array.isArray(shap.explanation.contributions) && shap.explanation.contributions.length > 0 ? (
                          <div style={{ marginTop: '16px', overflowX: 'auto' }}>
                            <table className="shap-table" style={{ width: "100%", textAlign: "left", borderCollapse: "collapse" }}>
                              <thead>
                                <tr style={{ borderBottom: "2px solid #ddd" }}>
                                  <th style={{ padding: "8px", fontWeight: '600' }}>Feature Name</th>
                                  <th style={{ padding: "8px", fontWeight: '600' }}>Contribution Value</th>
                                  <th style={{ padding: "8px", fontWeight: '600' }}>Effect</th>
                                </tr>
                              </thead>
                              <tbody>
                                {shap.explanation.contributions.map((c, i) => (
                                  <tr key={i} style={{ borderBottom: "1px solid #eee" }}>
                                    <td style={{ padding: "8px" }}>{c.feature_name}</td>
                                    <td style={{ padding: "8px" }}>{c.contribution.toFixed(4)}</td>
                                    <td style={{ padding: "8px" }}>
                                      <span style={{
                                        color: c.contribution > 0 ? '#4caf50' : c.contribution < 0 ? '#f44336' : '#777',
                                        fontWeight: '600',
                                        fontSize: '0.9rem'
                                      }}>
                                        {c.contribution > 0 ? `Supports ${prediction}` : c.contribution < 0 ? `Opposes ${prediction}` : "Neutral"}
                                      </span>
                                    </td>
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                          </div>
                        ) : (
                          <p style={{ marginTop: '10px' }}>No feature contributions available.</p>
                        )}
                      </details>
                    </div>
                  );
                })() : (
                  <p>Not applicable — SHAP explanation was not generated for this event.</p>
                )}
              </div>

              <div className="detail-section">
                <h3>INTEGRITY</h3>
                <p><strong>Record hash:</strong> {selectedLog.record_hash || 'N/A'}</p>
                <p><strong>Previous hash:</strong> {selectedLog.previous_hash || 'N/A'}</p>
                <p><strong>Hash verification status:</strong> {getHashVerificationStatus(selectedLog, verifyStatus)}</p>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default EvidenceLogView;
