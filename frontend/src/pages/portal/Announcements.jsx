import React from 'react';

import Card from '../../components/dashboard/Card';

const Announcements = () => (
  <div className="dashboard-container">
    <div className="page-heading-block">
      <p className="page-eyebrow">
        Workspace
      </p>

      <h1 className="page-title">
        Announcements
      </h1>

      <p className="page-subtitle">
        Company news and employee notices.
      </p>
    </div>

    <Card title="Company Announcements">
      <div className="announcement-list">
        <article>
          <strong>
            September Team Meeting
          </strong>
          <p>
            The monthly company meeting will be held
            on 8 September at 11:00 AM.
          </p>
        </article>

        <article>
          <strong>
            New HR Policy
          </strong>
          <p>
            Updated leave guidance is now available
            under Company Policies.
          </p>
        </article>

        <article>
          <strong>
            Scheduled IT Maintenance
          </strong>
          <p>
            Internal systems maintenance is planned
            for Saturday evening.
          </p>
        </article>

        <article>
          <strong>
            Employee Training Program
          </strong>
          <p>
            New internal learning modules are available
            to all employees.
          </p>
        </article>
      </div>

      <p className="demo-data-note">
        Announcement information is synthetic demonstration data.
      </p>
    </Card>
  </div>
);

export default Announcements;
