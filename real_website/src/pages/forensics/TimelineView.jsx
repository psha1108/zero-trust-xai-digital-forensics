import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import forensicsService from '../../services/forensicsService';
import { formatDateIST } from '../../utils/dateUtils';
import './Forensics.css';

const TimelineView = () => {
  const { sessionId } = useParams();
  const navigate = useNavigate();
  const [timeline, setTimeline] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

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

  useEffect(() => {
    const fetchTimeline = async () => {
      try {
        const data = await forensicsService.getTimeline(sessionId);
        setTimeline(data);
      } catch (err) {
        if (err.response?.status === 404) {
          setError('Session not found.');
        } else if (err.response?.status === 403) {
          setError('Forbidden: Admin access required.');
        } else {
          setError(err.response?.data?.error || 'Failed to fetch timeline');
        }
      } finally {
        setLoading(false);
      }
    };
    fetchTimeline();
  }, [sessionId]);

  if (loading) return <div className="forensics-container">Loading timeline...</div>;
  if (error) return <div className="forensics-container" style={{ color: 'red' }}>Error: {error}</div>;

  return (
    <div className="forensics-container">
      <div className="forensics-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h1 style={{ margin: 0 }}>Session Timeline</h1>
        <div>
          <button className="forensics-btn" onClick={() => navigate('/forensics')} style={{ marginRight: '10px' }}>Dashboard</button>
          <button className="forensics-btn primary" onClick={() => navigate(`/forensics/report/${sessionId}`)}>Generate Report</button>
        </div>
      </div>
      
      <p>Investigating Session: <strong>{sessionId}</strong></p>

      {timeline.length === 0 ? (
        <p>No events found for this session.</p>
      ) : (
        <div className="timeline-container">
          {timeline.map((event, idx) => {
            const isSuspicious = 
              (event.result && (event.result.toLowerCase() === 'blocked' || event.result.toLowerCase() === 'denied' || event.result.toLowerCase() === 'failed')) ||
              event.privilege_mismatch || 
              (event.risk_label && event.risk_label.toLowerCase() === 'high');

            return (
              <div key={idx} className={`timeline-item ${isSuspicious ? 'suspicious' : ''}`}>
                <div className="timeline-content">
                  <div className="timeline-meta">
                    {formatDateIST(event.timestamp)} • {event.event_type}
                  </div>
                  <h3 style={{ margin: '0 0 10px 0', color: isSuspicious ? '#dc3545' : 'inherit' }}>
                    {event.action}
                  </h3>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px', fontSize: '0.9em' }}>
                    <div>
                      <strong>User ID:</strong> {event.user_id}<br />
                      <strong>IP Address:</strong> {event.ip_address}<br />
                      <strong>Result:</strong> {event.result}
                      <br /><br />
                      {event.event_type === 'AccessEvent' && (
                        <div>
                          <strong>Policy Decision:</strong> {event.policy_decision || 'N/A'}<br />
                          <strong>Trigger/Reason:</strong> {getTriggers(event.policy_reason).join(', ')}
                        </div>
                      )}
                    </div>
                    <div>
                      {event.event_type === 'AccessEvent' ? (
                        <div>
                          <strong>ML Risk Assessment:</strong><br />
                          <span style={{display: 'inline-block', width: '60px'}}>RF Risk:</span> {event.risk_label === 'low' ? 'Low' : event.risk_label === 'medium' ? 'Medium' : event.risk_label === 'high' ? 'High' : (event.risk_label || 'N/A')}<br />
                          <span style={{display: 'inline-block', width: '60px'}}>IF:</span> {event.anomaly_score !== null ? (event.policy_reason && event.policy_reason.includes('isolation_forest_anomaly') ? 'Anomaly Detected' : 'Normal') : 'N/A'}<br />
                          <span style={{display: 'inline-block', width: '60px'}}>K-Means:</span> {event.cluster_id !== null ? `Cluster ${event.cluster_id}` : 'N/A'}
                        </div>
                      ) : (
                        <div style={{color: '#888'}}>Risk Assessment: Not applicable</div>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default TimelineView;
