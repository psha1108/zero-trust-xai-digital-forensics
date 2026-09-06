import React from 'react';
import ResourceView from '../../components/resources/ResourceView';
import resourceService from '../../services/resourceService';
import { DOCUMENTS } from '../../data/documents';

const NormalResource = () => {
  return (
    <ResourceView pageName="Documents" fetchFn={resourceService.getNormalResource}>
      <div style={{ padding: '10px' }}>
        <p style={{ marginBottom: '20px', fontSize: '1.1em' }}>Available Corporate Documents:</p>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '15px' }}>
          {DOCUMENTS.map(doc => (
            <div key={doc.id} style={{ border: '1px solid #ddd', padding: '15px', borderRadius: '5px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '5px' }}>
                <h3 style={{ margin: 0 }}>{doc.title}</h3>
                <span style={{ fontSize: '0.9em', color: '#666', backgroundColor: '#f0f0f0', padding: '2px 8px', borderRadius: '12px' }}>
                  {doc.category}
                </span>
              </div>
              <p style={{ margin: '5px 0 10px 0', color: '#444' }}>{doc.description}</p>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.9em' }}>
                <span style={{ color: doc.status === 'Available' ? 'green' : 'red' }}>Status: {doc.status}</span>
                <span style={{ color: '#888' }}>ID: {doc.id}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </ResourceView>
  );
};

export default NormalResource;
