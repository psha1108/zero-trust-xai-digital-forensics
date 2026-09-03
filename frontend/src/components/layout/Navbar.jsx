import React from 'react';

import { useAuth } from '../../hooks/useAuth';

import './Layout.css';

const Navbar = () => {
  const { user, logout } = useAuth();

  const handleLogout = async () => {
    await logout();
  };

  const displayRole = user?.role
    ? user.role
        .replaceAll('_', ' ')
        .replace(/\b\w/g, (letter) => letter.toUpperCase())
    : 'Employee';

  return (
    <nav className="navbar">
      <div className="navbar-brand">
        <span className="navbar-logo">
          ACME
        </span>

        <span className="navbar-title">
          Technologies
        </span>

        <span className="navbar-portal-label">
          Internal Corporate Portal
        </span>
      </div>

      <div className="navbar-user">
        <div className="user-info">
          <span className="user-name">
            {user?.username || 'Employee'}
          </span>

          <span className="user-role">
            {displayRole}
          </span>
        </div>

        <button
          className="btn-logout"
          onClick={handleLogout}
          type="button"
        >
          Logout
        </button>
      </div>
    </nav>
  );
};

export default Navbar;
