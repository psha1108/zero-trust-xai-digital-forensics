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
    
    // Automatic periodic SOC alert refresh
    const intervalId = setInterval(fetchAlerts, 5000);

    return () => {
      cancelled = true;
      clearInterval(intervalId);
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
                  Action
                </span>
                <span className="status-value">
                  {alert.action_taken || alert.policy_action || 'Unavailable'}
                </span>
              </div>

              {alert.termination_reason && (
                <div className="status-item">
                  <span className="status-label">
                    Termination Reason
                  </span>
                  <span className="status-value">
                    {alert.termination_reason}
                  </span>
                </div>
              )}

              {alert.session_outcome && (
                <div className="status-item">
                  <span className="status-label">
                    Session Outcome
                  </span>
                  <span className="status-value">
                    {alert.session_outcome}
                  </span>
                </div>
              )}

              <div className="status-item">
                <span className="status-label">
                  Why
                </span>
                <span className="status-value">
                  {alert.evidence_data?.zero_trust?.human_reason || 'Detailed policy reason unavailable for this event.'}
                </span>
              </div>

              {alert.alert_type === 'SESSION_TERMINATED' ? (
                <React.Fragment>
                  <h4 style={{ marginTop: '1rem', marginBottom: '0.5rem', fontSize: '0.9rem', fontWeight: 600 }}>ML Analysis</h4>
                  <div className="status-item">
                    <span className="status-label">Machine Learning</span>
                    <span className="status-value text-muted">N/A</span>
                  </div>

                  <h4 style={{ marginTop: '1rem', marginBottom: '0.5rem', fontSize: '0.9rem', fontWeight: 600 }}>XAI / SHAP</h4>
                  <div className="status-item">
                    <span className="status-label">Human explanation</span>
                    <span className="status-value text-muted">N/A</span>
                  </div>
                </React.Fragment>
              ) : (
                <React.Fragment>
                  <h4 style={{ marginTop: '1rem', marginBottom: '0.5rem', fontSize: '0.9rem', fontWeight: 600 }}>ML Analysis</h4>
                  
                  <div className="status-item">
                    <span className="status-label">
                      Random Forest
                    </span>
                    <span className="status-value">
                      {alert.evidence_data?.ml?.random_forest?.risk_label || 'Unavailable'} (Score: {typeof alert.evidence_data?.ml?.random_forest?.risk_score === 'number' ? alert.evidence_data.ml.random_forest.risk_score.toFixed(4) : 'Unavailable'})
                    </span>
                  </div>

                  <div className="status-item">
                    <span className="status-label">
                      Isolation Forest
                    </span>
                    <span className="status-value">
                      {alert.evidence_data?.ml?.isolation_forest?.is_anomaly ? 'Anomaly' : 'Normal'} (Score: {typeof alert.evidence_data?.ml?.isolation_forest?.anomaly_score === 'number' ? alert.evidence_data.ml.isolation_forest.anomaly_score.toFixed(4) : 'Unavailable'})
                    </span>
                  </div>

                  <div className="status-item">
                    <span className="status-label">
                      K-Means
                    </span>
                    <span className="status-value">
                      Cluster {alert.evidence_data?.ml?.kmeans?.cluster_id ?? 'Unknown'} - {alert.evidence_data?.ml?.kmeans?.behavior_label || 'Behavioural cluster information unavailable for this event.'}
                    </span>
                  </div>

                  <h4 style={{ marginTop: '1rem', marginBottom: '0.5rem', fontSize: '0.9rem', fontWeight: 600 }}>XAI / SHAP</h4>

                  <div className="status-item">
                    <span className="status-label">
                      Human explanation
                    </span>
                    <span className="status-value">
                      {alert.evidence_data?.shap?.human_explanation || 'Detailed SHAP explanation unavailable for this event.'}
                    </span>
                  </div>
                  
                  <div className="status-item">
                    <span className="status-label">
                      Contributors
                    </span>
                    <span className="status-value" style={{ fontSize: '0.85em', color: '#666' }}>
                      {alert.evidence_data?.shap?.contributions ? alert.evidence_data.shap.contributions.map(c => `${c.feature_name}: ${c.contribution > 0 ? '+' : ''}${c.contribution.toFixed(4)}`).join(', ') : 'Unavailable'}
                    </span>
                  </div>
                </React.Fragment>
              )}

              <h4 style={{ marginTop: '1rem', marginBottom: '0.5rem', fontSize: '0.9rem', fontWeight: 600 }}>Evidence</h4>
              
              <div className="status-item">
                <span className="status-label">
                  Event ID
                </span>
                <span className="status-value">
                  {alert.event_id}
                </span>
              </div>

              <div className="status-item">
                <span className="status-label">
                  Session ID
                </span>
                <span className="status-value" style={{ wordBreak: 'break-all', fontSize: '0.8em' }}>
                  {alert.session_id}
                </span>
              </div>
              
              <div className="status-item">
                <span className="status-label">
                  Evidence Reference
                </span>
                <span className="status-value" style={{ wordBreak: 'break-all', fontSize: '0.8em' }}>
                  {alert.evidence_data?.record_hash || 'Unavailable'}
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
