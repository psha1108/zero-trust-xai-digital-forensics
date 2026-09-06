import React from 'react';
import Card from '../../components/dashboard/Card';
import { ANNOUNCEMENTS } from '../../data/announcements';

const Announcements = () => {
  return (
    <div className="resource-view-container">
      <h1 className="page-title">Announcements</h1>
      
      <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
        {ANNOUNCEMENTS.map(ann => (
          <Card key={ann.id} title={ann.title}>
            <p style={{ margin: '10px 0', fontSize: '1.05em', lineHeight: '1.5' }}>{ann.content}</p>
            <div style={{ fontSize: '0.85em', color: '#888', marginTop: '15px' }}>
              Ref: {ann.id}
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
};

export default Announcements;
