import React, { useEffect, useState } from 'react';
import Card from './Card';
import dashboardService from '../../services/dashboardService';

const SessionStatusCard = () => {
  const [sessionStatus, setSessionStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let cancelled = false;

    const fetchSessionStatus = async () => {
      try {
        const data = await dashboardService.getSessionStatus();

        if (!cancelled) {
          setSessionStatus(data);
        }
      } catch {
        if (!cancelled) {
          setError('Failed to fetch session status.');
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    };

    fetchSessionStatus();

    return () => {
      cancelled = true;
    };
  }, []);

  const formatLoginTime = (value) => {
    if (!value) {
      return 'Unavailable';
    }

    const parsed = new Date(value);

    if (Number.isNaN(parsed.getTime())) {
      return value;
    }

    return parsed.toLocaleString();
  };

  return (
    <Card title="Session Status" className="widget-session">
      {loading ? (
        <div className="placeholder-text">Loading...</div>
      ) : error ? (
        <div className="placeholder-text error-text">{error}</div>
      ) : (
        <>
          <div className="status-item">
            <span className="status-label">Current User:</span>
            <span className="status-value highlight">
              {sessionStatus?.username || 'Unavailable'}
            </span>
          </div>

          <div className="status-item">
            <span className="status-label">Role Clearance:</span>
            <span className="status-value uppercase">
              {sessionStatus?.role || 'Unavailable'}
            </span>
          </div>

          <div className="status-item">
            <span className="status-label">Authentication:</span>
            <span className="status-value success">Verified</span>
          </div>

          <div className="status-item">
            <span className="status-label">Session State:</span>
            <span
              className={
                sessionStatus?.is_active
                  ? 'status-value success'
                  : 'status-value error-text'
              }
            >
              {sessionStatus?.is_active ? 'Active' : 'Inactive'}
            </span>
          </div>

          <div className="status-item">
            <span className="status-label">Login Time:</span>
            <span className="status-value">
              {formatLoginTime(sessionStatus?.started_at)}
            </span>
          </div>

          <div className="status-item">
            <span className="status-label">Current IP:</span>
            <span className="status-value">
              {sessionStatus?.current_ip || 'Unavailable'}
            </span>
          </div>

          <div className="status-item">
            <span className="status-label">Device Fingerprint:</span>
            <span className="status-value">
              {sessionStatus?.current_device_fingerprint || 'Unavailable'}
            </span>
          </div>
        </>
      )}
    </Card>
  );
};

export default SessionStatusCard;
