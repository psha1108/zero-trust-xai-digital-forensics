import React from 'react';

import Card from '../../components/dashboard/Card';
import ResourceView from '../../components/resources/ResourceView';
import resourceService from '../../services/resourceService';

const Policies = () => (
  <ResourceView
    pageName="Company Policies"
    subtitle="Employee policies and workplace guidance."
    fetchFn={resourceService.getPolicies}
  >
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
  </ResourceView>
);

export default Policies;
