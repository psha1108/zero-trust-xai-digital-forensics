import React from 'react';

import Card from '../../components/dashboard/Card';
import ResourceView from '../../components/resources/ResourceView';
import resourceService from '../../services/resourceService';

const Tasks = () => (
  <ResourceView
    pageName="My Tasks"
    subtitle="Your current ACME Technologies work items."
    fetchFn={resourceService.getTasks}
  >
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
  </ResourceView>
);

export default Tasks;
