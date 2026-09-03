import React, { useEffect, useState } from 'react';

import Card from './Card';
import dashboardService from '../../services/dashboardService';

const ActiveSessionsCard = () => {
  const [sessions, setSessions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let cancelled = false;

    const fetchActiveSessions = async () => {
      try {
        const data = await dashboardService.getActiveSessions();

        if (!cancelled) {
          setSessions(
            Array.isArray(data)
              ? data
              : []
          );
        }
      } catch {
        if (!cancelled) {
          setError(
            'Failed to fetch organization-wide active sessions.'
          );
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    };

    fetchActiveSessions();

    return () => {
      cancelled = true;
    };
  }, []);

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

  return (
    <Card
      title="Active Sessions"
      className="widget-session full-width"
    >
      {loading ? (
        <div className="placeholder-text">
          Loading...
        </div>
      ) : error ? (
        <div className="placeholder-text error-text">
          {error}
        </div>
      ) : sessions.length === 0 ? (
        <div className="placeholder-text">
          No active protected-application sessions.
        </div>
      ) : (
        <div style={{ overflowX: 'auto' }}>
          <table className="data-table">
            <thead>
              <tr>
                <th>User</th>
                <th>Role/Risk</th>
                <th>Session ID</th>
                <th>Started</th>
                <th>Current IP</th>
                <th>Risk Score</th>
                <th>Status</th>
              </tr>
            </thead>

            <tbody>
              {sessions.map((session) => (
                <tr key={session.session_id}>
                  <td>
                    {session.username || 'Unknown'}
                  </td>

                  <td>
                    {session.risk_label || 'Not analyzed'}
                  </td>

                  <td
                    style={{
                      fontFamily: 'monospace',
                    }}
                  >
                    {session.session_id || 'Unavailable'}
                  </td>

                  <td>
                    {formatTimestamp(session.started_at)}
                  </td>

                  <td>
                    {session.current_ip || 'Unavailable'}
                  </td>

                  <td>
                    {typeof session.risk_score === 'number'
                      ? session.risk_score.toFixed(4)
                      : 'Not analyzed'}
                  </td>

                  <td>
                    {session.is_active
                      ? 'Active'
                      : 'Inactive'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </Card>
  );
};

export default ActiveSessionsCard;