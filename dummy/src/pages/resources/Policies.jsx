import React, { useState } from 'react';
import Card from '../../components/dashboard/Card';
import { POLICIES } from '../../data/policies';

const PoliciesList = ({ policies, onSelect }) => {
  return (
    <div className="resource-grid">
      {policies.map(policy => (
        <div key={policy.id} className="resource-card-container">
          <Card className="resource-card-content">
            <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '10px' }}>
                <h3 style={{ margin: 0, fontSize: '1.1em', paddingRight: '10px' }}>{policy.title}</h3>
              </div>
              <p style={{ margin: '0 0 15px 0', color: 'var(--text-secondary)', fontSize: '0.9em', flexGrow: 1 }}>
                Category: {policy.category}
              </p>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85em', color: 'var(--text-secondary)', marginBottom: '10px' }}>
                <span>Version: {policy.version}</span>
                <span style={{ color: policy.status === 'Active' ? 'green' : '#d97706' }}>{policy.status}</span>
              </div>
              <div style={{ fontSize: '0.8em', color: '#999', borderTop: '1px solid var(--border-color)', paddingTop: '10px', marginTop: '10px' }}>
                Policy ID: {policy.id}
              </div>
              <button className="resource-btn" onClick={() => onSelect(policy)}>VIEW</button>
            </div>
          </Card>
        </div>
      ))}
    </div>
  );
};

const PolicyDetails = ({ policy, onBack }) => {
  return (
    <div>
      <button className="resource-btn-back" onClick={onBack}>
        &larr; BACK TO POLICIES
      </button>
      <Card>
        <div style={{ padding: '20px' }}>
          <h2 style={{ marginTop: 0, marginBottom: '10px', color: 'var(--primary-color)' }}>{policy.title}</h2>
          <div style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', marginBottom: '20px', display: 'flex', gap: '15px', flexWrap: 'wrap' }}>
            <span><strong>Policy ID:</strong> {policy.id}</span>
            <span><strong>Category:</strong> {policy.category}</span>
            <span><strong>Sensitivity:</strong> {policy.sensitivity}</span>
            <span><strong>Version:</strong> {policy.version}</span>
            <span><strong>Last Updated:</strong> {policy.lastUpdated}</span>
            <span><strong>Owner:</strong> {policy.owner}</span>
            <span><strong style={{color: policy.status === 'Active' ? 'green' : '#d97706'}}>{policy.status}</strong></span>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
            {policy.sections.map((section, idx) => (
              <div key={idx} style={{ borderTop: '1px solid var(--border-color)', paddingTop: '15px' }}>
                <h3 style={{ marginTop: 0, marginBottom: '10px' }}>{section.title}</h3>
                <p style={{ lineHeight: '1.6', margin: 0, whiteSpace: 'pre-wrap' }}>{section.content}</p>
              </div>
            ))}
          </div>
        </div>
      </Card>
    </div>
  );
};

const Policies = () => {
  const [selectedPolicy, setSelectedPolicy] = useState(null);

  return (
    <div className="resource-view-container">
      <h1 className="page-title">Company Policies</h1>
      {selectedPolicy ? (
        <PolicyDetails policy={selectedPolicy} onBack={() => setSelectedPolicy(null)} />
      ) : (
        <div>
          <p style={{ color: 'var(--text-secondary)', marginBottom: '24px' }}>Review important company policies and workplace guidelines.</p>
          <PoliciesList policies={POLICIES} onSelect={setSelectedPolicy} />
        </div>
      )}
    </div>
  );
};

export default Policies;
