import React from 'react';
import ResourceView from '../../components/resources/ResourceView';
import resourceService from '../../services/resourceService';
import { HR_DATA } from '../../data/hrData';

const HrResource = () => {
  return (
    <ResourceView pageName="HR & People" fetchFn={resourceService.getHrResource}>
      <div style={{ padding: '10px' }}>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px', marginBottom: '20px' }}>
          <div style={{ border: '1px solid #ddd', padding: '15px', borderRadius: '5px' }}>
            <h3 style={{ borderBottom: '1px solid #eee', paddingBottom: '10px', marginTop: 0 }}>Employee Information</h3>
            <p><strong>Employee ID:</strong> {HR_DATA.employeeInfo.id}</p>
            <p><strong>Department:</strong> {HR_DATA.employeeInfo.department}</p>
            <p><strong>Designation:</strong> {HR_DATA.employeeInfo.designation}</p>
            <p><strong>Manager:</strong> {HR_DATA.employeeInfo.manager}</p>
          </div>
          <div style={{ border: '1px solid #ddd', padding: '15px', borderRadius: '5px' }}>
            <h3 style={{ borderBottom: '1px solid #eee', paddingBottom: '10px', marginTop: 0 }}>Leave & Attendance</h3>
            <p><strong>Annual Leave:</strong> {HR_DATA.leaveAndAttendance.annualLeave} days</p>
            <p><strong>Used:</strong> {HR_DATA.leaveAndAttendance.used} days</p>
            <p><strong>Remaining:</strong> {HR_DATA.leaveAndAttendance.remaining} days</p>
          </div>
        </div>
        
        <div style={{ border: '1px solid #ddd', padding: '15px', borderRadius: '5px', marginBottom: '20px' }}>
          <h3 style={{ borderBottom: '1px solid #eee', paddingBottom: '10px', marginTop: 0 }}>Recent Attendance</h3>
          <ul style={{ listStyleType: 'none', padding: 0 }}>
            {HR_DATA.leaveAndAttendance.recentAttendance.map((record, idx) => (
              <li key={idx} style={{ padding: '5px 0', borderBottom: idx !== 4 ? '1px solid #f5f5f5' : 'none', display: 'flex', justifyContent: 'space-between' }}>
                <span>{record.day}</span>
                <span style={{ color: record.status === 'Present' ? 'green' : '#0056b3' }}>{record.status}</span>
              </li>
            ))}
          </ul>
        </div>
        
        <div style={{ border: '1px solid #ddd', padding: '15px', borderRadius: '5px' }}>
          <h3 style={{ borderBottom: '1px solid #eee', paddingBottom: '10px', marginTop: 0 }}>Benefits</h3>
          <ul style={{ paddingLeft: '20px', margin: 0 }}>
            {HR_DATA.benefits.map((benefit, idx) => (
              <li key={idx} style={{ padding: '3px 0' }}>{benefit}</li>
            ))}
          </ul>
        </div>
      </div>
    </ResourceView>
  );
};

export default HrResource;
