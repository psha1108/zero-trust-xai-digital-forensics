import React from 'react';
import Card from '../../components/dashboard/Card';
import { POLICIES } from '../../data/policies';

const Policies = () => {
  return (
    <div className="resource-view-container">
      <h1 className="page-title">Company Policies</h1>
      
      <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
        {POLICIES.map(policy => (
          <Card key={policy.id} title={policy.title}>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              <div><strong>Purpose:</strong> {policy.purpose}</div>
              <div><strong>Scope:</strong> {policy.scope}</div>
              <div><strong>Employee Responsibilities:</strong> {policy.responsibilities}</div>
              <div><strong>General Requirements:</strong> {policy.requirements}</div>
              <div><strong>Reporting:</strong> {policy.reporting}</div>
            </div>
            <div style={{ fontSize: '0.85em', color: '#888', marginTop: '15px', borderTop: '1px solid #eee', paddingTop: '10px' }}>
              Policy ID: {policy.id}
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
};

export default Policies;
