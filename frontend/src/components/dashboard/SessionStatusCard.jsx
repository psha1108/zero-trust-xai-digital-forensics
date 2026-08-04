import React from 'react';
import Card from './Card';
import { useAuth } from '../../hooks/useAuth';

const SessionStatusCard = () => {
  const { user } = useAuth();

  return (
    <Card title="Session Status" className="widget-session">
      <div className="status-item">
        <span className="status-label">Current User:</span>
        <span className="status-value highlight">{user?.username}</span>
      </div>
      <div className="status-item">
        <span className="status-label">Role Clearance:</span>
        <span className="status-value uppercase">{user?.role || 'Normal'}</span>
      </div>
      <div className="status-item">
        <span className="status-label">Authentication:</span>
        <span className="status-value success">Verified</span>
      </div>
      <div className="status-item">
        <span className="status-label">Session State:</span>
        <span className="status-value success">Active</span>
      </div>
      <div className="status-item">
        <span className="status-label">Login Time:</span>
        {/* Placeholder: missing backend data */}
        <span className="status-value text-muted">Unavailable</span>
      </div>
    </Card>
  );
};

export default SessionStatusCard;
