import React from 'react';
import { Link } from 'react-router-dom';

import Card from '../../components/dashboard/Card';

const ItSupport = () => (
  <div className="dashboard-container">
    <div className="page-heading-block">
      <p className="page-eyebrow">
        Departments
      </p>

      <h1 className="page-title">
        IT Support
      </h1>

      <p className="page-subtitle">
        Devices, support requests and account assistance.
      </p>
    </div>

    <div className="portal-content-grid">
      <Card title="My Devices">
        <p>
          Registered workstation
        </p>

        <p className="muted-text">
          Windows ? Chrome
        </p>
      </Card>

      <Card title="Support">
        <p>
          Raise an IT support request or review your
          existing support tickets.
        </p>

        <p className="positive-text">
          No open tickets
        </p>
      </Card>

      <Card title="Account Access">
        <p>
          Review your current portal session and
          account activity.
        </p>

        <Link to="/sessions">
          View My Sessions ?
        </Link>
      </Card>
    </div>

    <p className="demo-data-note">
      Device and support-ticket descriptions are synthetic
      demonstration content. Session information is retrieved
      from the project backend.
    </p>
  </div>
);

export default ItSupport;
