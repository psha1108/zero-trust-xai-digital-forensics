import React from 'react';

import Card from '../../components/dashboard/Card';
import ResourceView from '../../components/resources/ResourceView';
import resourceService from '../../services/resourceService';

const ManagementReportsResource = () => (
  <ResourceView
    pageName="Management Reports"
    subtitle="Internal management reporting and planning resources."
    fetchFn={resourceService.getManagementReports}
  >
    <Card title="Management Reports">
      <p>
        Authorized management reporting resources
        are available to your account.
      </p>
    </Card>
  </ResourceView>
);

export default ManagementReportsResource;
