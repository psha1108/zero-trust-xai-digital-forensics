import React from 'react';

import Card from '../../components/dashboard/Card';
import ResourceView from '../../components/resources/ResourceView';
import resourceService from '../../services/resourceService';

const HrResource = () => (
  <ResourceView
    pageName="HR & People"
    subtitle="Employee information, leave, benefits and HR requests."
    fetchFn={resourceService.getHrResource}
  >
    <div className="portal-content-grid">
      <Card title="My Information">
        <p>
          Operations Department
        </p>

        <p>
          Employment Status: Active
        </p>
      </Card>

      <Card title="Leave">
        <div className="portal-stat">
          <strong>12</strong>
          <span>Days available</span>
        </div>

        <p>
          View leave history or submit a new leave request.
        </p>
      </Card>

      <Card title="Benefits">
        <ul className="business-list">
          <li>Employee benefits overview</li>
          <li>Medical benefit information</li>
          <li>Company leave policies</li>
        </ul>
      </Card>

      <Card title="HR Requests">
        <p>
          No open HR requests.
        </p>
      </Card>
    </div>
  </ResourceView>
);

export default HrResource;
