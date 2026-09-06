import React from 'react';
import { useAuth } from '../../hooks/useAuth';
import Card from '../../components/dashboard/Card';
import { CURRENT_EMPLOYEE } from '../../data/employees';

const Profile = () => {
  const { user } = useAuth();

  return (
    <div>
      <h1 className="page-title">User Profile</h1>
      <Card>
        <div className="profile-container" style={{ padding: '20px' }}>
          <h2 style={{ borderBottom: '1px solid #ccc', paddingBottom: '10px', marginBottom: '20px' }}>Personal Information</h2>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '15px', fontSize: '1.1em' }}>
            <div><strong>Name:</strong> {CURRENT_EMPLOYEE.name}</div>
            <div><strong>Employee ID:</strong> {CURRENT_EMPLOYEE.id}</div>
            <div><strong>Department:</strong> {CURRENT_EMPLOYEE.department}</div>
            <div><strong>Designation:</strong> {CURRENT_EMPLOYEE.designation}</div>
            <div><strong>Manager:</strong> {CURRENT_EMPLOYEE.manager}</div>
            <div><strong>Office:</strong> {CURRENT_EMPLOYEE.office}</div>
            <div><strong>Status:</strong> {CURRENT_EMPLOYEE.status}</div>
            <div style={{ marginTop: '10px' }}>
              <h3 style={{ borderBottom: '1px solid #eee', paddingBottom: '5px', marginBottom: '10px' }}>Contact</h3>
              <strong>Email:</strong> {CURRENT_EMPLOYEE.email}
            </div>
            
            <div style={{ marginTop: '20px', padding: '10px', backgroundColor: '#f9f9f9', borderRadius: '5px' }}>
              <strong>System Auth:</strong> Authenticated as {user?.username} ({user?.role})
            </div>
          </div>
        </div>
      </Card>
    </div>
  );
};

export default Profile;
