import React from 'react';

import Card from '../../components/dashboard/Card';
import { useAuth } from '../../hooks/useAuth';

const Profile = () => {
  const { user } = useAuth();

  const idNumber = user?.id
    ? String(1000 + Number(user.id))
    : '1001';

  const role = user?.role === 'admin'
    ? 'Administrator'
    : 'Employee';

  const username = user?.username || 'employee';

  return (
    <div className="dashboard-container">
      <div className="page-heading-block">
        <p className="page-eyebrow">
          Account
        </p>

        <h1 className="page-title">
          My Profile
        </h1>

        <p className="page-subtitle">
          Your ACME Technologies employee information.
        </p>
      </div>

      <Card title="Employee Information">
        <div className="profile-detail-grid">
          <div>
            <span className="profile-label">
              Name
            </span>

            <strong>
              {username}
            </strong>
          </div>

          <div>
            <span className="profile-label">
              Employee ID
            </span>

            <strong>
              EMP-{idNumber}
            </strong>
          </div>

          <div>
            <span className="profile-label">
              Department
            </span>

            <strong>
              Operations
            </strong>
          </div>

          <div>
            <span className="profile-label">
              Role
            </span>

            <strong>
              {role}
            </strong>
          </div>

          <div>
            <span className="profile-label">
              Email
            </span>

            <strong>
              {username}@acme-demo.com
            </strong>
          </div>

          <div>
            <span className="profile-label">
              Account
            </span>

            <strong className="positive-text">
              Active
            </strong>
          </div>
        </div>

        <p className="demo-data-note">
          Employee profile details shown here are synthetic
          demonstration data for the ACME Technologies portal.
        </p>
      </Card>
    </div>
  );
};

export default Profile;
