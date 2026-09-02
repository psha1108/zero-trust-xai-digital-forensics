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
              </tr>
            </thead>
            <tbody>
              {evidence.map(log => (
                <tr key={log.id}>
                  <td>{log.id}</td>
                  <td>{formatDateIST(log.created_at)}</td>
                  <td>{log.details?.event_type || 'Unknown'}</td>
                  <td>{log.login_event_id}</td>
                  <td style={{ fontFamily: 'monospace', fontSize: '0.85em' }}>
                    {log.record_hash ? log.record_hash.substring(0, 16) + '...' : 'N/A'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

export default EvidenceLogView;
