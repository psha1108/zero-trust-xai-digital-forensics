import React, { useState } from 'react';
import ResourceView from '../../components/resources/ResourceView';
import resourceService from '../../services/resourceService';
import Card from '../../components/dashboard/Card';
import { HR_DATA } from '../../data/hrData';

const HrList = ({ documents, onSelect }) => {
  return (
    <div className="resource-grid">
      {documents.map(doc => (
        <div key={doc.id} className="resource-card-container">
          <Card className="resource-card-content">
            <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '10px' }}>
                <h3 style={{ margin: 0, fontSize: '1.1em', paddingRight: '10px' }}>{doc.title}</h3>
              </div>
              <p style={{ margin: '0 0 15px 0', color: 'var(--text-secondary)', fontSize: '0.9em', flexGrow: 1 }}>
                {doc.description}
              </p>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85em', color: 'var(--text-secondary)', marginBottom: '10px' }}>
                <span>Version: {doc.version}</span>
              </div>
              <div style={{ fontSize: '0.8em', color: '#999', borderTop: '1px solid var(--border-color)', paddingTop: '10px', marginTop: '10px' }}>
                Document ID: {doc.id}
              </div>
              <button className="resource-btn" onClick={() => onSelect(doc)}>VIEW</button>
            </div>
          </Card>
        </div>
      ))}
    </div>
  );
};

const HrDetails = ({ doc, onBack }) => {
  return (
    <div>
      <button className="resource-btn-back" onClick={onBack}>
        &larr; BACK TO HR & PEOPLE
      </button>
      <Card>
        <div style={{ padding: '20px' }}>
          <h2 style={{ marginTop: 0, marginBottom: '10px', color: 'var(--primary-color)' }}>{doc.title}</h2>
          <div style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', marginBottom: '20px', display: 'flex', gap: '15px', flexWrap: 'wrap' }}>
            <span><strong>Document ID:</strong> {doc.id}</span>
            <span><strong>Category:</strong> {doc.category}</span>
            <span><strong>Sensitivity:</strong> {doc.sensitivity}</span>
            <span><strong>Version:</strong> {doc.version}</span>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
            {doc.sections.map((section, idx) => (
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

const HrResource = () => {
  const [selectedDoc, setSelectedDoc] = useState(null);

  return (
    <ResourceView pageName="HR & People" fetchFn={resourceService.getHrResource}>
      {selectedDoc ? (
        <HrDetails doc={selectedDoc} onBack={() => setSelectedDoc(null)} />
      ) : (
        <div style={{ padding: '10px' }}>
          <p style={{ color: 'var(--text-secondary)', marginBottom: '24px', fontSize: '1.05em' }}>Access employee resources, policies, and benefits information.</p>
          <HrList documents={HR_DATA} onSelect={setSelectedDoc} />
        </div>
      )}
    </ResourceView>
  );
};

export default HrResource;
