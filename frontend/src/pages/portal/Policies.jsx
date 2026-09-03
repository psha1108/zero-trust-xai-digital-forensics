import React from 'react';

import Card from '../../components/dashboard/Card';

const Policies = () => (
  <div className="dashboard-container">
    <div className="page-heading-block">
      <p className="page-eyebrow">
        Workspace
      </p>

      <h1 className="page-title">
        Company Policies
      </h1>

      <p className="page-subtitle">
        Employee policies and workplace guidance.
      </p>
    </div>

    <Card title="Policy Library">
      <div className="document-list">
        <div>
          <span>??</span>
          <strong>Employee Handbook</strong>
        </div>

        <div>
          <span>??</span>
          <strong>Leave Policy</strong>
        </div>

        <div>
          <span>??</span>
          <strong>Information Security Policy</strong>
        </div>

        <div>
          <span>??</span>
          <strong>Acceptable Use Policy</strong>
        </div>

        <div>
          <span>??</span>
          <strong>Workplace Conduct</strong>
        </div>

        <div>
          <span>??</span>
          <strong>Remote Work Policy</strong>
        </div>
      </div>

      <p className="demo-data-note">
        Policy documents are synthetic demonstration content.
      </p>
    </Card>
  </div>
);

export default Policies;
