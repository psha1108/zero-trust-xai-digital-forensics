import React, { useEffect, useState } from 'react';
import Card from './Card';
import dashboardService from '../../services/dashboardService';

const SecurityStateCard = () => {
  const [securityState, setSecurityState] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let cancelled = false;

    const fetchSecurityState = async () => {
      try {
        const data = await dashboardService.getSecurityState();

        if (!cancelled) {
          setSecurityState(data);
        }
      } catch {
        if (!cancelled) {
          setError('Failed to fetch security state.');
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    };

    fetchSecurityState();

    return () => {
      cancelled = true;
    };
  }, []);

  const displayValue = (value) => {
    if (
      value === null
      || value === undefined
      || value === ''
    ) {
      return 'Unavailable';
    }

    return String(value);
  };

  const formatRiskScore = (value) => {
    if (
      value === null
      || value === undefined
    ) {
      return 'Unavailable';
    }

    const numericValue = Number(value);

    if (!Number.isFinite(numericValue)) {
      return String(value);
    }

    return numericValue.toFixed(4);
  };

  const formatTimestamp = (value) => {
    if (!value) {
      return 'Unavailable';
    }

    const parsed = new Date(value);

    if (Number.isNaN(parsed.getTime())) {
      return value;
    }

    return parsed.toLocaleString();
  };

  const formatPrivilegeMismatch = (value) => {
    if (value === null || value === undefined) {
      return 'Unavailable';
    }

    return value ? 'Yes' : 'No';
  };

  return (
    <Card title="Risk Analysis" className="widget-risk">
      {loading ? (
        <div className="placeholder-text">Loading...</div>
      ) : error ? (
        <div className="placeholder-text error-text">{error}</div>
      ) : !securityState?.has_analysis ? (
        <>
          <div className="placeholder-text">
            No security analysis available yet
          </div>

          <div className="status-item">
            <span className="status-label">Session State:</span>
            <span
              className={
                securityState?.is_active
                  ? 'status-value success'
                  : 'status-value error-text'
              }
            >
              {securityState?.is_active ? 'Active' : 'Inactive'}
            </span>
          </div>
        </>
      ) : (
        <>
          <div className="status-item">
            <span className="status-label">RF Risk Label:</span>
            <span className="status-value uppercase">
              {displayValue(securityState.risk_label)}
            </span>
          </div>

          <div className="status-item">
            <span className="status-label">
              RF High-Risk Probability:
            </span>
            <span className="status-value highlight">
              {formatRiskScore(securityState.risk_score)}
            </span>
          </div>

          <div className="status-item">
            <span className="status-label">
              Isolation Forest Anomaly Score:
            </span>
            <span className="status-value">
              {displayValue(securityState.anomaly_score)}
            </span>
          </div>

          <div className="status-item">
            <span className="status-label">
              Behavioral Cluster:
            </span>
            <span className="status-value">
              {displayValue(securityState.cluster_id)}
            </span>
          </div>

          <div className="status-item">
            <span className="status-label">
              Latest Policy Action:
            </span>
            <span className="status-value">
              {displayValue(securityState.latest_action)}
            </span>
          </div>

          <div className="status-item">
            <span className="status-label">
              Latest Resource:
            </span>
            <span className="status-value">
              {displayValue(securityState.latest_resource)}
            </span>
          </div>

          <div className="status-item">
            <span className="status-label">
              Latest Access:
            </span>
            <span className="status-value">
              {formatTimestamp(securityState.latest_access_at)}
            </span>
          </div>

          <div className="status-item">
            <span className="status-label">
              Privilege Mismatch:
            </span>
            <span className="status-value">
              {formatPrivilegeMismatch(
                securityState.privilege_mismatch
              )}
            </span>
          </div>

          <div className="status-item">
            <span className="status-label">Session State:</span>
            <span
              className={
                securityState.is_active
                  ? 'status-value success'
                  : 'status-value error-text'
              }
            >
              {securityState.is_active ? 'Active' : 'Inactive'}
            </span>
          </div>
        </>
      )}
    </Card>
  );
};

export default SecurityStateCard;
