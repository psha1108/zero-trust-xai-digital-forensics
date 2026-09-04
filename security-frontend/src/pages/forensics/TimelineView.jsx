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
                    </div>
                    <div>
                      {event.privilege_mismatch && <div style={{color: '#dc3545'}}>Privilege Mismatch!</div>}
                      {event.risk_label ? (
                        <div><strong>Risk:</strong> {event.risk_label} (Score: {event.risk_score || event.anomaly_score})</div>
                      ) : (
                        <div style={{color: '#888'}}>Risk Assessment: Not available</div>
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
