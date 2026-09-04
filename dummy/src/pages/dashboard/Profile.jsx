import React from 'react';
import { useAuth } from '../../hooks/useAuth';
import Card from '../../components/dashboard/Card';

const Profile = () => {
  const { user } = useAuth();

  return (
    <div>
      <h1 className="page-title">User Profile</h1>
      <Card>
        <div className="profile-container" style={{ padding: '20px' }}>
          <h2 style={{ borderBottom: '1px solid #ccc', paddingBottom: '10px', marginBottom: '20px' }}>Investigator Information</h2>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '15px', fontSize: '1.1em' }}>
            <div>
              <strong>Username:</strong> {user?.username || 'Not available'}
            </div>
            <div>
              <strong>Role:</strong> {user?.role === 'admin' ? (
                <span style={{ color: '#0d6efd', fontWeight: 'bold' }}>ADMIN</span>
              ) : (
                <span>{user?.role || 'Not available'}</span>
              )}
            </div>
            <div>
              <strong>Authentication Status:</strong> {user ? 'Authenticated securely' : 'Not authenticated'}
            </div>
            <div>
              <strong>Email:</strong> {user?.email || 'Not available'}
            </div>
            <div>
              <strong>Account Created:</strong> {user?.created_at ? new Date(user.created_at).toLocaleString() : 'Not available'}
            </div>
          </div>
          <p style={{ marginTop: '30px', color: '#666', fontStyle: 'italic', fontSize: '0.9em' }}>
            Profile editing functionality is locked to preserve authentication integrity.
          </p>
        </div>
      </Card>
    </div>
  );
};

export default Profile;
