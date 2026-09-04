import React from 'react';

import Card from '../../components/dashboard/Card';
import ResourceView from '../../components/resources/ResourceView';
import resourceService from '../../services/resourceService';

const AdminResource = () => (
  <ResourceView
    pageName="Administration"
    subtitle="Administrative functions for authorized portal administrators."
    fetchFn={resourceService.getAdminResource}
  >
    <div className="portal-content-grid">
      <Card title="Portal Administration">
        <p>
          Administrative workspace available to
          authorized ACME Technologies administrators.
        </p>
      </Card>

      <Card title="Account Management">
        <p>
          Administrative account and access-management functions.
        </p>
      </Card>
    </div>
  </ResourceView>
);

export default AdminResource;
