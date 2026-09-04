import React, { useEffect, useState } from 'react';
import Card from './Card';
import dashboardService from '../../services/dashboardService';

const LoginHistoryTable = () => {
  const [history, setHistory] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchHistory = async () => {
      try {
        const data = await dashboardService.getLoginHistory();
        setHistory(data);
      } catch (err) {
        setError('Failed to fetch login history.');
      } finally {
        setLoading(false);
      }
    };

    fetchHistory();
  }, []);

  return (
    <Card title="Recent Login Activity" className="widget-logins full-width">
      <table className="data-table">
        <thead>
          <tr>
            <th>Timestamp</th>
            <th>Username</th>
            <th>Status</th>
            <th>IP Address</th>
            <th>Device</th>
          </tr>
        </thead>
        <tbody>
          {loading ? (
            <tr>
              <td colSpan="5" className="placeholder-text">Loading...</td>
            </tr>
          ) : error ? (
            <tr>
              <td colSpan="5" className="placeholder-text error-text">{error}</td>
            </tr>
          ) : history && history.length > 0 ? (
            history.map((entry, index) => (
              <tr key={index}>
                <td>{entry.timestamp}</td>
                <td>{entry.username}</td>
                <td>{entry.status}</td>
                <td>{entry.ip_address}</td>
                <td>{entry.device}</td>
              </tr>
            ))
          ) : (
            <tr>
              <td colSpan="5" className="placeholder-text">No login history available</td>
            </tr>
          )}
        </tbody>
      </table>
    </Card>
  );
};

export default LoginHistoryTable;
