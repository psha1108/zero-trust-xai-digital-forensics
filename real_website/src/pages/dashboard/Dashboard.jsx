import React from 'react';
import Card from '../../components/dashboard/Card';
import SessionStatusCard from '../../components/dashboard/SessionStatusCard';
import LoginHistoryTable from '../../components/dashboard/LoginHistoryTable';
import AccessHistoryTable from '../../components/dashboard/AccessHistoryTable';
import SecurityAlertsCard from '../../components/dashboard/SecurityAlertsCard';
import './Dashboard.css';

const Dashboard = () => {
  return (
    <div className="dashboard-container">
      <h1 className="page-title">Security Overview</h1>
      
      <div className="dashboard-grid">
        {/* 1. Session Status */}
        <SessionStatusCard />

        {/* 4. Security Alerts */}
        <SecurityAlertsCard />

        {/* 5. Risk Score (Placeholder) */}
        <Card title="Risk Analysis" className="widget-risk">
          <div className="placeholder-text">Risk Analysis Not Available Yet</div>
        </Card>

        {/* 6. Digital Forensics (Placeholder) */}
        <Card title="Digital Forensics" className="widget-forensics">
          <div className="placeholder-text">No forensic investigation generated.</div>
        </Card>

        {/* 2. Recent Login Activity */}
        <LoginHistoryTable />

        {/* 3. Recent Resource Access */}
        <AccessHistoryTable />
      </div>
    </div>
  );
};

export default Dashboard;
