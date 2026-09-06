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
  const [selectedLog, setSelectedLog] = useState(null);
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
                <th>Risk</th>
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
                  <td>{log.risk || 'Not available'}</td>
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
                <p><strong>Event ID:</strong> {selectedLog.event_id || 'Not available'}</p>
                <p><strong>Event Type:</strong> {selectedLog.event_type}</p>
                <p><strong>Timestamp:</strong> {selectedLog.timestamp ? formatDateIST(selectedLog.timestamp) : 'Not available'}</p>
              </div>

              <div className="detail-section">
                <h3>SESSION</h3>
                <p><strong>Session ID:</strong> {selectedLog.session_id || 'Not available'}</p>
                <p><strong>Login Event ID:</strong> {selectedLog.login_event_id || 'Not available'}</p>
              </div>

              <div className="detail-section">
                <h3>USER</h3>
                <p><strong>User ID:</strong> {selectedLog.details?.user?.user_id || 'Not available'}</p>
                <p><strong>Username:</strong> {selectedLog.user || 'Not available'}</p>
                <p><strong>Role:</strong> {selectedLog.details?.user?.role || 'Not available'}</p>
              </div>

              <div className="detail-section">
                <h3>ACCESS</h3>
                <p><strong>Resource:</strong> {selectedLog.resource || 'Not available'}</p>
                <p><strong>Sensitivity:</strong> {selectedLog.details?.resource?.sensitivity || 'Not available'}</p>
                <p><strong>Request Count:</strong> {selectedLog.details?.access?.request_count ?? 'Not available'}</p>
                <p><strong>Unauthorized Access:</strong> {selectedLog.details?.access?.unauthorized_access !== undefined ? String(selectedLog.details?.access?.unauthorized_access) : 'Not available'}</p>
                <p><strong>Privilege Mismatch:</strong> {selectedLog.details?.security?.privilege_mismatch !== undefined ? String(selectedLog.details?.security?.privilege_mismatch) : 'Not available'}</p>
              </div>

              <div className="detail-section">
                <h3>NETWORK / DEVICE</h3>
                <p><strong>IP Address:</strong> {selectedLog.details?.network?.ip_address || selectedLog.details?.ip_address || 'Not available'}</p>
                <p><strong>Device ID:</strong> {selectedLog.details?.device?.device_id || selectedLog.details?.device_info || 'Not available'}</p>
                <p><strong>Device Fingerprint:</strong> {selectedLog.details?.device?.device_fingerprint || 'Not available'}</p>
                <p><strong>IP Changed:</strong> {selectedLog.details?.network?.ip_changed_during_session !== undefined ? String(selectedLog.details?.network?.ip_changed_during_session) : 'Not available'}</p>
                <p><strong>Device Changed:</strong> {selectedLog.details?.device?.device_changed_during_session !== undefined ? String(selectedLog.details?.device?.device_changed_during_session) : 'Not available'}</p>
              </div>

              <div className="detail-section">
                <h3>ML RISK</h3>
                <p><strong>Isolation Forest anomaly score/status:</strong> {selectedLog.details?.ml?.isolation_forest?.anomaly_score ?? 'Not available'} / {selectedLog.details?.ml?.isolation_forest?.status || 'Not available'}</p>
                <p><strong>Random Forest risk label:</strong> {selectedLog.risk || 'Not available'}</p>
                <p><strong>Random Forest risk score/probabilities:</strong> {selectedLog.details?.ml?.random_forest?.risk_score ?? 'Not available'} {selectedLog.details?.ml?.random_forest?.probabilities ? `(${JSON.stringify(selectedLog.details.ml.random_forest.probabilities)})` : ''}</p>
                <p><strong>K-Means cluster:</strong> {selectedLog.details?.ml?.kmeans?.cluster_id ?? 'Not available'}</p>
                <p><strong>Behavioral label:</strong> {selectedLog.details?.ml?.behavioral?.label || 'Not available'}</p>
              </div>

              <div className="detail-section">
                <h3>SHAP</h3>
                <p><strong>Stored SHAP explanation:</strong> {selectedLog.details?.shap?.explanation || 'Not available'}</p>
                {selectedLog.details?.shap && selectedLog.details.shap.feature_contributions && Object.keys(selectedLog.details.shap.feature_contributions).length > 0 ? (
                  <table className="shap-table">
                    <thead>
                      <tr>
                        <th>Feature</th>
                        <th>Value</th>
                        <th>Contribution</th>
                      </tr>
                    </thead>
                    <tbody>
                      {Object.entries(selectedLog.details.shap.feature_contributions).map(([feature, contribution]) => (
                        <tr key={feature}>
                          <td>{feature}</td>
                          <td>N/A</td>
                          <td>{contribution !== undefined ? Number(contribution).toFixed(4) : 'N/A'}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                ) : (
                  <p><strong>Feature contributions:</strong> Not available</p>
                )}
              </div>

              <div className="detail-section">
                <h3>ZERO TRUST</h3>
                <p><strong>Policy decision:</strong> {selectedLog.policy_decision || 'Not available'}</p>
                <p><strong>Reason:</strong> {selectedLog.details?.zero_trust?.reason || 'Not available'}</p>
                <p><strong>Action taken:</strong> {selectedLog.details?.zero_trust?.action_taken || 'Not available'}</p>
                <p><strong>HTTP status:</strong> {selectedLog.details?.zero_trust?.http_status || 'Not available'}</p>
              </div>

              <div className="detail-section">
                <h3>INTEGRITY</h3>
                <p><strong>Record hash:</strong> {selectedLog.record_hash || 'Not available'}</p>
                <p><strong>Previous hash:</strong> {selectedLog.previous_hash || 'Not available'}</p>
                <p><strong>Hash verification status:</strong> {selectedLog.details?.integrity?.hash_verification_status || 'Not available'}</p>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default EvidenceLogView;
