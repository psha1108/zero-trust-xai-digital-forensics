import React from 'react';
import { useAuth } from '../../hooks/useAuth';
import './Layout.css';

const Navbar = () => {
  const { user, logout } = useAuth();

  const handleLogout = async () => {
    await logout();
  };

  return (
    <nav className="navbar">
      <div className="navbar-brand">
        <span className="navbar-logo">ACME</span>
        <span className="navbar-title">Organization Portal</span>
      </div>
      <div className="navbar-user">
        <div className="user-info">
          <span className="user-name">{user?.username || 'Guest'}</span>
          <span className="user-role">{user?.role || 'No Role'}</span>
        </div>
        <button className="btn-logout" onClick={handleLogout}>
          Logout
        </button>
      </div>
    </nav>
  );
};

export default Navbar;
