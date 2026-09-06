import React, { useEffect, useState } from 'react';
import Card from '../dashboard/Card';
import './ResourceView.css';

const ResourceView = ({ fetchFn, pageName, children }) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const loadResource = async () => {
      try {
        const responseData = await fetchFn();
        setData(responseData);
      } catch (err) {
        const status = err.response?.status;
        const payload = err.response?.data;
        const policyAction = payload?.policy_action;

        if (status === 403 || policyAction === 'Restrict') {
          setError('Access Restricted. Your account does not have the required permissions.');
        } else if (status === 401 && policyAction === 'Block') {
          setError('Access Blocked.');
        } else if (status === 401 && policyAction === 'OTP') {
          setError('Additional verification required.');
        } else if (payload?.error) {
          setError(payload.error);
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
          <div className={`placeholder-text error-text ${error.includes('Restricted') || error.includes('Blocked') ? 'restricted-access-ui' : ''}`} role="alert" style={error.includes('Restricted') || error.includes('Blocked') ? { padding: '40px', textAlign: 'center', backgroundColor: error.includes('Blocked') ? '#450a0a' : '#fff1f2', border: error.includes('Blocked') ? '1px solid #7f1d1d' : '1px solid #fecdd3', borderRadius: '8px' } : {}}>
            {(error.includes('Restricted') || error.includes('Blocked')) && (
              <h2 style={{ color: error.includes('Blocked') ? '#fca5a5' : '#be123c', marginTop: 0, marginBottom: '15px' }}>{error.includes('Blocked') ? 'Access Blocked' : 'Access Restricted'}</h2>
            )}
            <p style={error.includes('Restricted') || error.includes('Blocked') ? { color: error.includes('Blocked') ? '#fecaca' : '#881337', margin: 0, fontWeight: error.includes('Blocked') ? 'bold' : 'normal' } : {}}>{error}</p>
          </div>
        ) : data ? (
          children ? children : (
            <div className="resource-data">
              <h2 className="resource-title">{data.title}</h2>
              <p className="resource-message">{data.message}</p>
            </div>
          )
        ) : null}
      </Card>
    </div>
  );
};

export default ResourceView;
