import React, { useEffect, useState } from 'react';
import Card from './Card';
import dashboardService from '../../services/dashboardService';
import { formatDateIST } from '../../utils/dateUtils';

const SecurityAlertsCard = () => {
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let cancelled = false;

    const fetchAlerts = async () => {
      try {
        const data = await dashboardService.getSecurityAlerts();

        if (cancelled) {
          return;
        }

        setAlerts(
          Array.isArray(data)
            ? data
            : []
        );
      } catch {
        if (!cancelled) {
          setError(
            'Failed to fetch security alerts.'
          );
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    };

    fetchAlerts();

    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <Card
      title="Security Alerts"
      className="widget-alerts"
    >
      {loading ? (
        <div className="placeholder-text">
          Loading...
        </div>
      ) : error ? (
        <div className="placeholder-text error-text">
          {error}
        </div>
      ) : alerts.length === 0 ? (
        <div className="placeholder-text">
          No active alerts.
        </div>
      ) : (
        <div className="alerts-list">
          {alerts.map((alert) => (
            <div
              key={alert.event_id}
              className="alert-item"
            >
              <div className="status-item">
                <span className="status-label">
                  Time
                </span>
                <span className="status-value text-muted">
                  {alert.timestamp
                    ? formatDateIST(alert.timestamp)
                    : 'Unavailable'}
                </span>
              </div>

              <div className="status-item">
                <span className="status-label">
                  Severity
                </span>
                <span className="status-value uppercase">
                  {alert.severity}
                </span>
              </div>

              <div className="status-item">
                <span className="status-label">
                  Alert Type
                </span>
                <span className="status-value">
                  {alert.alert_type}
                </span>
              </div>

              <div className="status-item">
                <span className="status-label">
                  Message
                </span>
                <span className="status-value">
                  {alert.message}
                </span>
              </div>

              <div className="status-item">
                <span className="status-label">
                  Resource
                </span>
                <span className="status-value">
                  {alert.resource || 'Unavailable'}
                </span>
              </div>

              <div className="status-item">
                <span className="status-label">
                  Policy Action
                </span>
                <span className="status-value">
                  {alert.policy_action || 'Unavailable'}
                </span>
              </div>

              <div className="status-item">
                <span className="status-label">
                  RF High-Risk Probability
                </span>
                <span className="status-value">
                  {typeof alert.risk_score === 'number'
                    ? alert.risk_score.toFixed(4)
                    : 'Unavailable'}
                </span>
              </div>

              <div className="status-item">
                <span className="status-label">
                  Privilege Mismatch
                </span>
                <span className="status-value">
                  {alert.privilege_mismatch
                    ? 'Yes'
                    : 'No'}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </Card>
  );
};

export default SecurityAlertsCard;
