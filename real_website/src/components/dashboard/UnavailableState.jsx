import React from 'react';
import Card from './Card';
import './UnavailableState.css';

const UnavailableState = ({ title, message }) => {
  return (
    <div className="unavailable-state-container">
      <h1 className="page-title">{title}</h1>
      <Card>
        <div className="unavailable-content" style={{ padding: '2rem', textAlign: 'center' }}>
          <h3 style={{ marginBottom: '1rem' }}>Organization Security Monitoring</h3>
          <p style={{ marginBottom: '1rem', color: '#666' }}>
            This security-console capability is ready at the frontend layer but requires the corresponding organization-wide backend API.
          </p>
          <p style={{ fontWeight: 'bold', color: '#d9534f' }}>
            Backend capability currently unavailable.
          </p>
          {message && <p style={{ marginTop: '1rem', fontStyle: 'italic', color: '#888' }}>{message}</p>}
        </div>
      </Card>
    </div>
  );
};

export default UnavailableState;
