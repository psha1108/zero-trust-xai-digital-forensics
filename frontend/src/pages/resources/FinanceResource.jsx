import React from 'react';

import Card from '../../components/dashboard/Card';
import ResourceView from '../../components/resources/ResourceView';
import resourceService from '../../services/resourceService';

const FinanceResource = () => (
  <ResourceView
    pageName="Finance"
    subtitle="Payslips, expense claims and employee financial information."
    fetchFn={resourceService.getFinanceResource}
  >
    <div className="portal-content-grid">
      <Card title="My Payslips">
        <ul className="business-list">
          <li>August 2026</li>
          <li>July 2026</li>
          <li>June 2026</li>
        </ul>
      </Card>

      <Card title="Expense Claims">
        <p>
          Submit an expense claim or review your
          recent reimbursement requests.
        </p>

        <p className="muted-text">
          No pending claims.
        </p>
      </Card>

      <Card title="Financial Information">
        <ul className="business-list">
          <li>Salary information</li>
          <li>Reimbursement policy</li>
          <li>Travel expense policy</li>
        </ul>
      </Card>
    </div>
  </ResourceView>
);

export default FinanceResource;
