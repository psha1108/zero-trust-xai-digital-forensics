import React, { useEffect, useState } from 'react';
import Card from './Card';
import dashboardService from '../../services/dashboardService';

const AccessHistoryTable = () => {
  const [history, setHistory] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchHistory = async () => {
      try {
        const data = await dashboardService.getAccessHistory();
        setHistory(data);
      } catch (err) {
        setError('Failed to fetch access history.');
      } finally {
        setLoading(false);
      }
    };

    fetchHistory();
  }, []);

  return (
    <Card title="Recent Resource Access" className="widget-access full-width">
      <table className="data-table">
        <thead>
          <tr>
            <th>Timestamp</th>
            <th>Resource</th>
            <th>Sensitivity</th>
            <th>IP Address</th>
            <th>Device Changed</th>
            <th>IP Changed</th>
          </tr>
        </thead>
        <tbody>
          {loading ? (
            <tr>
              <td colSpan="6" className="placeholder-text">Loading...</td>
            </tr>
          ) : error ? (
            <tr>
              <td colSpan="6" className="placeholder-text error-text">{error}</td>
            </tr>
          ) : history && history.length > 0 ? (
            history.map((entry, index) => (
              <tr key={index}>
                <td>{entry.timestamp}</td>
                <td>{entry.resource}</td>
                <td>{entry.sensitivity}</td>
                <td>{entry.ip_address}</td>
                <td>{entry.device_changed ? 'Yes' : 'No'}</td>
                <td>{entry.ip_changed ? 'Yes' : 'No'}</td>
              </tr>
            ))
          ) : (
            <tr>
              <td colSpan="6" className="placeholder-text">No access history available</td>
            </tr>
          )}
        </tbody>
      </table>
    </Card>
  );
};

export default AccessHistoryTable;
