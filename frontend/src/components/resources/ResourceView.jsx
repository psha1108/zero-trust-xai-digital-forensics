import React, { useEffect, useState } from 'react';
import Card from '../dashboard/Card';
import './ResourceView.css';

const ResourceView = ({ fetchFn, pageName }) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const loadResource = async () => {
      try {
        const responseData = await fetchFn();
        setData(responseData);
      } catch (err) {
        if (err.response && err.response.status === 403) {
          setError('403 Forbidden: You do not have clearance to access this resource.');
        } else if (err.response && err.response.data && err.response.data.error) {
          setError(err.response.data.error);
        } else {
          setError('Secure connection failed. Unable to retrieve resource.');
        }
      } finally {
        setLoading(false);
      }
    };
    
    loadResource();
  }, [fetchFn]);

  return (
    <div className="resource-view-container">
      <h1 className="page-title">{pageName}</h1>
      <Card>
        {loading ? (
          <div className="placeholder-text">Establishing secure connection...</div>
        ) : error ? (
          <div className="placeholder-text error-text" role="alert">{error}</div>
        ) : data ? (
          <div className="resource-data">
            <h2 className="resource-title">{data.title}</h2>
            <div className="resource-meta">
              <span className="status-label">Classification: </span>
              <span className={`status-value uppercase sensitivity-${data.sensitivity}`}>
                {data.sensitivity}
              </span>
            </div>
            <p className="resource-message">{data.message}</p>
          </div>
        ) : null}
      </Card>
    </div>
  );
};

export default ResourceView;
