import React from 'react';

import Card from '../../components/dashboard/Card';

const Tasks = () => (
  <div className="dashboard-container">
    <div className="page-heading-block">
      <p className="page-eyebrow">
        Workspace
      </p>

      <h1 className="page-title">
        My Tasks
      </h1>

      <p className="page-subtitle">
        Your current ACME Technologies work items.
      </p>
    </div>

    <Card title="Assigned Tasks">
      <div className="task-list">
        <div>
          <strong>
            Complete Security Awareness Training
          </strong>
          <span>
            Due 10 Sep 2026
          </span>
        </div>

        <div>
          <strong>
            Review Updated IT Policy
          </strong>
          <span>
            Due 12 Sep 2026
          </span>
        </div>

        <div>
          <strong>
            Submit Monthly Operations Report
          </strong>
          <span>
            Due 15 Sep 2026
          </span>
        </div>
      </div>

      <p className="demo-data-note">
        Task information is synthetic demonstration data.
      </p>
    </Card>
  </div>
);

export default Tasks;
