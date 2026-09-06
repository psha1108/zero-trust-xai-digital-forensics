import React, { useEffect, useState } from 'react';
import Card from '../../components/dashboard/Card';
import axiosInstance from '../../api/axios';

const MySessions = () => {
  const [sessionInfo, setSessionInfo] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchSessionStatus = async () => {
      try {
        const response = await axiosInstance.get('/dashboard/session-status');
        setSessionInfo(response.data);
      } catch (err) {
        setError('Unable to fetch active session details.');
      } finally {
        setLoading(false);
      }
    };
    fetchSessionStatus();
  }, []);

  return (
    <div className="resource-view-container">
      <h1 className="page-title">My Sessions</h1>
      
      <Card title="Current Session">
        {loading ? (
          <div>Loading session data...</div>
        ) : error ? (
          <div className="error-text">{error}</div>
        ) : sessionInfo ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '15px' }}>
            <div style={{ display: 'grid', gridTemplateColumns: '150px 1fr', gap: '10px' }}>
              <strong>Status:</strong>
              <span style={{ color: sessionInfo.is_active ? 'green' : 'red' }}>
                {sessionInfo.is_active ? 'Active' : 'Inactive'}
              </span>
              
              <strong>Login Time:</strong>
              <span>{sessionInfo.started_at ? new Date(sessionInfo.started_at).toLocaleString() : 'N/A'}</span>
              
              <strong>Device:</strong>
              <span>{sessionInfo.current_device_fingerprint || 'Unknown'}</span>
              
              <strong>IP Address:</strong>
              <span>{sessionInfo.current_ip || 'Unknown'}</span>
              
              <strong>Session ID:</strong>
              <span style={{ fontFamily: 'monospace', fontSize: '0.9em' }}>{sessionInfo.session_id}</span>
            </div>
          </div>
        ) : (
          <div>No active session details available.</div>
        )}
      </Card>
    </div>
  );
};

export default MySessions;
