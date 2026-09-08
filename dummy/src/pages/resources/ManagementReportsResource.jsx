import React, { useState } from 'react';
import ResourceView from '../../components/resources/ResourceView';
import resourceService from '../../services/resourceService';
import Card from '../../components/dashboard/Card';
import { MANAGEMENT_REPORTS } from '../../data/managementReports';

const ReportsList = ({ reports, onSelect }) => {
  return (
    <div className="resource-grid">
      {reports.map(report => (
        <div key={report.id} className="resource-card-container">
          <Card className="resource-card-content">
            <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '10px' }}>
                <h3 style={{ margin: 0, fontSize: '1.1em', paddingRight: '10px' }}>{report.title}</h3>
                <span style={{ fontSize: '0.8em', backgroundColor: report.sensitivity === 'High' ? '#fee2e2' : '#fef3c7', color: report.sensitivity === 'High' ? '#991b1b' : '#92400e', padding: '2px 6px', borderRadius: '4px' }}>
                  {report.sensitivity}
                </span>
              </div>
              <p style={{ margin: '0 0 15px 0', color: 'var(--text-secondary)', fontSize: '0.9em', flexGrow: 1 }}>
                Department: {report.department}
              </p>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85em', color: 'var(--text-secondary)', marginBottom: '10px' }}>
                <span>Period: {report.reportingPeriod}</span>
                <span style={{ color: report.status === 'Finalized' ? 'green' : '#d97706' }}>{report.status}</span>
              </div>
              <div style={{ fontSize: '0.8em', color: '#999', borderTop: '1px solid var(--border-color)', paddingTop: '10px', marginTop: '10px' }}>
                Report ID: {report.id}
              </div>
              <button className="resource-btn" onClick={() => onSelect(report)}>VIEW</button>
            </div>
          </Card>
        </div>
      ))}
    </div>
  );
};

const ReportDetails = ({ report, onBack }) => {
  return (
    <div>
      <button className="resource-btn-back" onClick={onBack}>
        &larr; BACK TO REPORTS
      </button>
      <Card>
        <div style={{ padding: '20px' }}>
          <h2 style={{ marginTop: 0, marginBottom: '10px', color: 'var(--primary-color)' }}>{report.title}</h2>
          <div style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', marginBottom: '20px', display: 'flex', gap: '15px', flexWrap: 'wrap' }}>
            <span><strong>Report ID:</strong> {report.id}</span>
            <span><strong>Department:</strong> {report.department}</span>
            <span><strong>Period:</strong> {report.reportingPeriod}</span>
            <span><strong>Sensitivity:</strong> {report.sensitivity}</span>
            <span><strong style={{color: report.status === 'Finalized' ? 'green' : '#d97706'}}>{report.status}</strong></span>
          </div>

          <div style={{ borderTop: '1px solid var(--border-color)', paddingTop: '20px', marginBottom: '20px' }}>
            <h3 style={{ marginTop: 0, marginBottom: '10px' }}>Executive Summary</h3>
            <p style={{ lineHeight: '1.6' }}>{report.executiveSummary}</p>
          </div>

          <div style={{ borderTop: '1px solid var(--border-color)', paddingTop: '20px', marginBottom: '20px' }}>
            <h3 style={{ marginTop: 0, marginBottom: '10px' }}>Key Highlights</h3>
            <ul style={{ lineHeight: '1.6', paddingLeft: '20px' }}>
              {report.keyHighlights.map((item, idx) => (
                <li key={idx}>{item}</li>
              ))}
            </ul>
          </div>

          <div style={{ borderTop: '1px solid var(--border-color)', paddingTop: '20px', marginBottom: '20px' }}>
            <h3 style={{ marginTop: 0, marginBottom: '10px' }}>Operational Overview</h3>
            <p style={{ lineHeight: '1.6' }}>{report.operationalOverview}</p>
          </div>

          <div style={{ borderTop: '1px solid var(--border-color)', paddingTop: '20px' }}>
            <h3 style={{ marginTop: 0, marginBottom: '10px' }}>Next-Quarter Focus</h3>
            <p style={{ lineHeight: '1.6' }}>{report.nextQuarterFocus}</p>
          </div>
        </div>
      </Card>
    </div>
  );
};

const ManagementReportsResource = () => {
  const [selectedReport, setSelectedReport] = useState(null);

  return (
    <ResourceView pageName="Management Reports" fetchFn={resourceService.getManagementReportsResource}>
      {selectedReport ? (
        <ReportDetails report={selectedReport} onBack={() => setSelectedReport(null)} />
      ) : (
        <div style={{ padding: '10px' }}>
          <p style={{ color: 'var(--text-secondary)', marginBottom: '24px', fontSize: '1.05em' }}>Executive and Departmental Performance Reports:</p>
          <ReportsList reports={MANAGEMENT_REPORTS} onSelect={setSelectedReport} />
        </div>
      )}
    </ResourceView>
  );
};

export default ManagementReportsResource;
