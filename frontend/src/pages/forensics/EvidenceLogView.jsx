import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import forensicsService from '../../services/forensicsService';
import { formatDateIST } from '../../utils/dateUtils';
import './Forensics.css';

const EvidenceLogView = () => {
  const [evidence, setEvidence] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [verifyStatus, setVerifyStatus] = useState(null);
  const [verifying, setVerifying] = useState(false);
  const navigate = useNavigate();

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
        <div style={{ overflowX: 'auto' }}>
          <table className="forensics-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Timestamp</th>
                <th>Event Type</th>
                <th>Login Event ID</th>
                <th>Record Hash</th>
                <th>SHAP Details</th>
              </tr>
            </thead>
            <tbody>
              {evidence.map(log => {
                const eventType = log.details?.event?.event_type || log.details?.event_type || 'Unknown';
                const shap = log.details?.shap;
                const isSessionTerm = eventType === 'SessionTermination';

                return (
                  <tr key={log.id}>
                    <td>{log.id}</td>
                    <td>{formatDateIST(log.created_at)}</td>
                    <td>{eventType}</td>
                    <td>{log.login_event_id}</td>
                    <td style={{ fontFamily: 'monospace', fontSize: '0.85em' }}>
                      {log.record_hash ? log.record_hash.substring(0, 16) + '...' : 'N/A'}
                    </td>
                    <td>
                      {isSessionTerm ? (
                        <span style={{ color: '#888' }}>SHAP: Not applicable for this event</span>
                      ) : shap ? (
                        <details>
                          <summary style={{ cursor: 'pointer', color: '#0056b3' }}>View SHAP</summary>
                          <div style={{ fontSize: '0.85em', marginTop: '5px', padding: '5px', backgroundColor: '#f8f9fa', borderRadius: '4px' }}>
                            <p style={{ margin: '0 0 5px 0' }}><strong>RF Prediction:</strong> {shap.prediction || 'N/A'} (Prob: {shap.model_probability})</p>
                            <p style={{ margin: '0 0 5px 0' }}><strong>Base Value:</strong> {shap.explanation?.base_value?.toFixed(4) || 'N/A'}</p>
                            <div style={{ margin: '0 0 5px 0' }}>
                              <strong>Contributions:</strong>
                              <ul style={{ margin: '2px 0', paddingLeft: '20px' }}>
                                {shap.explanation?.contributions?.map((c, i) => (
                                  <li key={i}>{c.feature_name}: {c.contribution > 0 ? '+' : ''}{c.contribution.toFixed(4)}</li>
                                )) || <li>N/A</li>}
                              </ul>
                            </div>
                            <p style={{ margin: '0', fontStyle: 'italic' }}>
                              <strong>Human-readable explanation:</strong><br/>
                              {shap.human_explanation || 'Detailed SHAP explanation unavailable for this event.'}
                            </p>
                          </div>
                        </details>
                      ) : (
                        <span style={{ color: '#888' }}>SHAP: Not available</span>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

export default EvidenceLogView;
