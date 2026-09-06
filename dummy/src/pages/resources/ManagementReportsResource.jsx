import React from 'react';
import ResourceView from '../../components/resources/ResourceView';
import resourceService from '../../services/resourceService';
import { MANAGEMENT_REPORTS } from '../../data/managementReports';

const ManagementReportsResource = () => {
  return (
    <ResourceView pageName="Management Reports" fetchFn={resourceService.getManagementReportsResource}>
      <div style={{ padding: '10px' }}>
        <p style={{ marginBottom: '20px', fontSize: '1.1em' }}>Executive and Departmental Performance Reports:</p>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '15px' }}>
          {MANAGEMENT_REPORTS.map(report => (
            <div key={report.id} style={{ border: '1px solid #ddd', padding: '15px', borderRadius: '5px', display: 'flex', flexDirection: 'column' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '10px' }}>
                <h3 style={{ margin: 0, fontSize: '1.1em' }}>{report.title}</h3>
                <span style={{ fontSize: '0.8em', backgroundColor: report.sensitivity === 'High' ? '#fee2e2' : '#fef3c7', color: report.sensitivity === 'High' ? '#991b1b' : '#92400e', padding: '2px 6px', borderRadius: '4px' }}>
                  {report.sensitivity}
                </span>
              </div>
              <p style={{ margin: '0 0 15px 0', color: '#555', flexGrow: 1 }}>{report.description}</p>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.9em', color: '#666', borderTop: '1px solid #eee', paddingTop: '10px' }}>
                <span>Period: {report.reportingPeriod}</span>
                <span style={{ color: report.status === 'Finalized' ? 'green' : '#d97706' }}>{report.status}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </ResourceView>
  );
};

export default ManagementReportsResource;
