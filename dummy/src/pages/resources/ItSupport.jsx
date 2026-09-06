import React from 'react';
import Card from '../../components/dashboard/Card';
import { IT_SUPPORT_DATA } from '../../data/itSupport';

const ItSupport = () => {
  return (
    <div className="resource-view-container">
      <h1 className="page-title">IT Support</h1>
      
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px', marginBottom: '20px' }}>
        <Card title="My Devices">
          <ul style={{ listStyleType: 'none', padding: 0 }}>
            {IT_SUPPORT_DATA.devices.map(device => (
              <li key={device.id} style={{ padding: '10px 0', borderBottom: '1px solid #eee' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <strong>{device.type}</strong>
                  <span style={{ color: device.status === 'Active' ? 'green' : '#0056b3' }}>{device.status}</span>
                </div>
                <div style={{ fontSize: '0.9em', color: '#666' }}>{device.id}</div>
              </li>
            ))}
          </ul>
        </Card>
        
        <Card title="Quick Help">
          <ul style={{ paddingLeft: '20px' }}>
            {IT_SUPPORT_DATA.quickHelp.map((help, idx) => (
              <li key={idx} style={{ padding: '5px 0' }}>
                <a href="#" style={{ color: '#0056b3', textDecoration: 'none' }}>{help}</a>
              </li>
            ))}
          </ul>
        </Card>
      </div>

      <Card title="Support Requests">
        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          {IT_SUPPORT_DATA.supportRequests.map(req => (
            <div key={req.id} style={{ display: 'flex', justifyContent: 'space-between', padding: '15px', backgroundColor: '#f9f9f9', borderRadius: '4px', border: '1px solid #ddd' }}>
              <div>
                <strong style={{ display: 'block', marginBottom: '5px' }}>{req.issue}</strong>
                <span style={{ fontSize: '0.9em', color: '#666' }}>{req.id}</span>
              </div>
              <span style={{ 
                alignSelf: 'center',
                padding: '4px 10px', 
                borderRadius: '12px', 
                fontSize: '0.9em',
                backgroundColor: req.status === 'Resolved' ? '#dcfce7' : '#fef9c3',
                color: req.status === 'Resolved' ? '#166534' : '#854d0e'
              }}>
                {req.status}
              </span>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
};

export default ItSupport;
