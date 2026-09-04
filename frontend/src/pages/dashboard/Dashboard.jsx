import React from 'react';
import { Link } from 'react-router-dom';

import Card from '../../components/dashboard/Card';
import { useAuth } from '../../hooks/useAuth';

import './Dashboard.css';

const Dashboard = () => {
  const { user } = useAuth();

  const displayName = user?.username || 'Employee';

  return (
    <div className="dashboard-container">
      <div className="page-heading-block">
        <p className="page-eyebrow">
          ACME Technologies
        </p>

        <h1 className="page-title">
          Welcome back, {displayName}
        </h1>

        <p className="page-subtitle">
          Operations Department ? Employee Portal
        </p>
      </div>

      <div className="dashboard-grid">
        <Card title="Quick Access">
          <div className="portal-link-list">
            <Link to="/documents">
              Company Documents ?
            </Link>

            <Link to="/tasks">
              My Tasks ?
            </Link>

            <Link to="/hr">
              HR &amp; People ?
            </Link>

            <Link to="/it-support">
              IT Support ?
            </Link>
          </div>
        </Card>

        <Card title="My Tasks">
          <div className="portal-stat">
            <strong>3</strong>
            <span>Pending tasks</span>
          </div>

          <p>
            One task is due within the next seven days.
          </p>

          <Link to="/tasks">
            View Tasks ?
          </Link>
        </Card>

        <Card title="My Sessions">
          <div className="portal-status-row">
            <span className="portal-status-dot" />
            <span>
              Current session active
            </span>
          </div>

          <p>
            Review your current account session and
            recent sign-in information.
          </p>

          <Link to="/sessions">
            View Sessions ?
          </Link>
        </Card>

        <Card
          title="Recent Activity"
          className="full-width"
        >
          <ul className="portal-activity-list">
            <li>
              Viewed Employee Handbook
            </li>

            <li>
              Checked Company Policies
            </li>

            <li>
              Reviewed assigned tasks
            </li>
          </ul>
        </Card>

        <Card
          title="Announcements"
          className="full-width"
        >
          <div className="announcement-preview-list">
            <div>
              <strong>
                September Team Meeting
              </strong>
              <span>
                Monthly all-hands meeting scheduled for 8 September.
              </span>
            </div>

            <div>
              <strong>
                Updated Leave Policy
              </strong>
              <span>
                The revised leave policy is now available in Company Policies.
              </span>
            </div>

            <div>
              <strong>
                Scheduled IT Maintenance
              </strong>
              <span>
                Internal systems maintenance is planned this weekend.
              </span>
            </div>
          </div>

          <Link to="/announcements">
            View All Announcements ?
          </Link>
        </Card>
      </div>
    </div>
  );
};

export default Dashboard;
