import React, { useEffect, useState } from 'react';
import Card from './Card';
import dashboardService from '../../services/dashboardService';

const SecurityAlertsCard = () => {
  const [alerts, setAlerts] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchAlerts = async () => {
      try {
        const data = await dashboardService.getSecurityAlerts();
        setAlerts(data);
      } catch (err) {
        setError('Failed to fetch security alerts.');
      } finally {
        setLoading(false);
      }
    };

    fetchAlerts();
  }, []);

  return (
    <Card title="Security Alerts" className="widget-alerts">
      {loading ? (
        <div className="placeholder-text">Loading...</div>
      ) : error ? (
        <div className="placeholder-text error-text">{error}</div>
      ) : alerts && alerts.length > 0 ? (
        <ul className="alerts-list">
          {alerts.map((alert, index) => (
            <li key={index} className="alert-item">
              <span className="alert-time">{alert.timestamp}</span>
              <span className="alert-message">{alert.message}</span>
            </li>
          ))}
        </ul>
      ) : (
        <div className="placeholder-text">No active alerts.</div>
      )}
    </Card>
  );
};

export default SecurityAlertsCard;
