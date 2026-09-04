import React from 'react';
import { Link } from 'react-router-dom';

import Card from '../../components/dashboard/Card';
import ResourceView from '../../components/resources/ResourceView';
import resourceService from '../../services/resourceService';

const NormalResource = () => (
  <ResourceView
    pageName="Company Documents"
    subtitle="Policies, handbooks and shared company resources."
    fetchFn={resourceService.getNormalResource}
  >
    <div className="portal-content-grid">
      <Card title="Company Documents">
        <div className="document-list">
          <div>
            <span>??</span>
            <div>
              <strong>Employee Handbook</strong>
              <small>Company guide for all employees</small>
            </div>
          </div>

          <div>
            <span>??</span>
            <div>
              <strong>Code of Conduct</strong>
              <small>Professional conduct guidelines</small>
            </div>
          </div>

          <div>
            <span>??</span>
            <div>
              <strong>Leave Policy</strong>
              <small>Leave eligibility and procedures</small>
            </div>
          </div>

          <div>
            <span>??</span>
            <div>
              <strong>IT Usage Policy</strong>
              <small>Acceptable use of company systems</small>
            </div>
          </div>

          <div>
            <span>??</span>
            <div>
              <strong>Department Documents</strong>
              <small>Operations team resources</small>
            </div>
          </div>
        </div>
      </Card>

      <Card title="Restricted Resources">
        <div className="restricted-resource-row">
          <div>
            <span aria-hidden="true">??</span>
          </div>

          <div>
            <strong>
              Management Reports
            </strong>

            <p>
              Internal management reporting for
              authorized personnel.
            </p>

            <Link
              to="/resources/management-reports"
            >
              Request Access ?
            </Link>
          </div>
        </div>
      </Card>
    </div>
  </ResourceView>
);

export default NormalResource;
