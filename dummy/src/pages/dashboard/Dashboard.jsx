import React from 'react';
import SessionStatusCard from '../../components/dashboard/SessionStatusCard';
import './Dashboard.css';

const Dashboard = () => {
  return (
    <div className="dashboard-container">
      <h1 className="page-title">Organization Dashboard</h1>
      
      <div className="dashboard-grid">
        {/* 1. Session Status */}
        <SessionStatusCard />
      </div>
    </div>
  );
};

export default Dashboard;
