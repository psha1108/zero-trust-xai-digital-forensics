import React from 'react';
import SessionStatusCard from '../../components/dashboard/SessionStatusCard';
import LoginHistoryTable from '../../components/dashboard/LoginHistoryTable';
import AccessHistoryTable from '../../components/dashboard/AccessHistoryTable';
import SecurityAlertsCard from '../../components/dashboard/SecurityAlertsCard';
import SecurityStateCard from '../../components/dashboard/SecurityStateCard';
import DigitalForensicsCard from '../../components/dashboard/DigitalForensicsCard';
import './Dashboard.css';

const Dashboard = () => {
  return (
    <div className="dashboard-container">
      <h1 className="page-title">Security Operations Overview</h1>
      
      <div className="dashboard-grid">
        {/* 1. Session Status */}
        <SessionStatusCard />

        {/* 4. Security Alerts */}
        <SecurityAlertsCard />

        {/* 5. Persisted Security State */}
        <SecurityStateCard />

        {/* 6. Digital Forensics */}
        <DigitalForensicsCard />

        {/* 2. Recent Login Activity */}
        <LoginHistoryTable />

        {/* 3. Recent Resource Access */}
        <AccessHistoryTable />
      </div>
    </div>
  );
};

export default Dashboard;
