import React from 'react';
import { Link } from 'react-router-dom';

import Card from '../../components/dashboard/Card';
import { useAuth } from '../../hooks/useAuth';

import './Dashboard.css';

const Dashboard = () => {
  const { user } = useAuth();

  return (
    <div className="dashboard-container">
      <h1 className="page-title">
        Corporate Portal
      </h1>

      <div className="dashboard-grid">
        <Card
          title="Welcome"
          className="full-width"
        >
          <p>
            Welcome, <strong>{user?.username || 'User'}</strong>.
          </p>

          <p>
            Signed-in role:{' '}
            <strong>{user?.role || 'Not available'}</strong>
          </p>

          <p>
            Use the portal to access organizational
            documents and resources available to your account.
          </p>
        </Card>

        <Card title="General Documents">
          <p>
            Access general organizational information
            and shared documents.
          </p>

          <Link to="/resources/normal">
            Open General Documents
          </Link>
        </Card>

        <Card title="HR Documents">
          <p>
            Access human-resources documents and
            employee information.
          </p>

          <Link to="/resources/hr">
            Open HR Documents
          </Link>
        </Card>

        <Card title="Finance Reports">
          <p>
            Access finance-related reports and
            protected financial resources.
          </p>

          <Link to="/resources/finance">
            Open Finance Reports
          </Link>
        </Card>

        <Card title="Admin Controls">
          <p>
            Administrative functions are protected
            according to your assigned access privileges.
          </p>

          <Link to="/resources/admin">
            Open Admin Controls
          </Link>
        </Card>
      </div>
    </div>
  );
};

export default Dashboard;
