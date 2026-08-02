import React, { useEffect, useState } from 'react';
import { useAuth } from '../../hooks/useAuth';
import Card from '../../components/dashboard/Card';
import './Dashboard.css';
// import dashboardService from '../../services/dashboardService';

const Dashboard = () => {
  const { user } = useAuth();
  
  // TODO: Fetch real data from backend when endpoints are ready
  // const [loginHistory, setLoginHistory] = useState([]);
  // const [accessHistory, setAccessHistory] = useState([]);

  return (
    <div className="dashboard-container">
      <h1 className="page-title">Security Overview</h1>
      
      <div className="dashboard-grid">
        {/* 1. Session Status */}
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
            <span className="status-value text-muted">Awaiting backend data...</span>
          </div>
        </Card>

        {/* 4. Security Alerts (Placeholder) */}
        <Card title="Security Alerts" className="widget-alerts">
          <div className="placeholder-text">No active alerts.</div>
        </Card>

        {/* 5. Risk Score (Placeholder) */}
        <Card title="Risk Analysis" className="widget-risk">
          <div className="placeholder-text">Risk Analysis Not Available Yet</div>
        </Card>

        {/* 6. Digital Forensics (Placeholder) */}
        <Card title="Digital Forensics" className="widget-forensics">
          <div className="placeholder-text">No forensic investigation generated.</div>
        </Card>

        {/* 2. Recent Login Activity */}
        <Card title="Recent Login Activity" className="widget-logins full-width">
          {/* TODO: Connect to backend /api/logins endpoint if it exists */}
          <table className="data-table">
            <thead>
              <tr>
                <th>Username</th>
                <th>Timestamp</th>
                <th>Status</th>
                <th>IP Address</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td colSpan="4" className="placeholder-text">Awaiting backend connection...</td>
              </tr>
            </tbody>
          </table>
        </Card>

        {/* 3. Recent Resource Access */}
        <Card title="Recent Resource Access" className="widget-access full-width">
          {/* TODO: Connect to backend /api/access-events endpoint if it exists */}
          <table className="data-table">
            <thead>
              <tr>
                <th>Resource</th>
                <th>Sensitivity</th>
                <th>Timestamp</th>
                <th>Device</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td colSpan="4" className="placeholder-text">Awaiting backend connection...</td>
              </tr>
            </tbody>
          </table>
        </Card>
      </div>
    </div>
  );
};

export default Dashboard;
