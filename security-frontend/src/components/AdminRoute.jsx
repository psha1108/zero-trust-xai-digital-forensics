import React from 'react';
import { Outlet } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';

const AdminRoute = () => {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="loading-container">
        Loading security authorization...
      </div>
    );
  }

  if (!user || user.role !== 'admin') {
    return (
      <div
        style={{
          padding: '2rem',
          maxWidth: '700px',
        }}
      >
        <h1>
          Security Console Access Denied
        </h1>

        <p>
          The AI Security Operations Console is
          restricted to authorized security
          administrators.
        </p>

        <p>
          Application users should use the
          Protected Organization Portal instead.
        </p>
      </div>
    );
  }

  return <Outlet />;
};

export default AdminRoute;
