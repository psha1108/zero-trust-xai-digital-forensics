import React from 'react';

import Card from '../../components/dashboard/Card';
import ResourceView from '../../components/resources/ResourceView';
import resourceService from '../../services/resourceService';

const Announcements = () => (
  <ResourceView
    pageName="Announcements"
    subtitle="Company news and employee notices."
    fetchFn={resourceService.getAnnouncements}
  >
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
  </ResourceView>
);

export default Announcements;
