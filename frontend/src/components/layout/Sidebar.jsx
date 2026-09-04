import React from 'react';
import { NavLink } from 'react-router-dom';

import { useAuth } from '../../hooks/useAuth';

import './Layout.css';

const Sidebar = () => {
  const { user, logout } = useAuth();

  const handleLogout = async () => {
    await logout();
  };

  const linkClass = ({ isActive }) =>
    `nav-link ${isActive ? 'active' : ''}`;

  const isAdmin = user?.role === 'admin';

  return (
    <aside className="sidebar">
      <nav className="sidebar-nav">
        <div className="nav-section">
          <h3 className="nav-heading">
            Main
          </h3>

          <NavLink
            to="/dashboard"
            className={linkClass}
          >
            <span aria-hidden="true">?</span>
            <span>Dashboard</span>
          </NavLink>

          <NavLink
            to="/profile"
            className={linkClass}
          >
            <span aria-hidden="true">?</span>
            <span>My Profile</span>
          </NavLink>
        </div>

        <div className="nav-section">
          <h3 className="nav-heading">
            Workspace
          </h3>

          <NavLink
            to="/documents"
            className={linkClass}
          >
            <span aria-hidden="true">?</span>
            <span>Documents</span>
          </NavLink>

          <NavLink
            to="/tasks"
            className={linkClass}
          >
            <span aria-hidden="true">?</span>
            <span>My Tasks</span>
          </NavLink>

          <NavLink
            to="/announcements"
            className={linkClass}
          >
            <span aria-hidden="true">?</span>
            <span>Announcements</span>
          </NavLink>

          <NavLink
            to="/policies"
            className={linkClass}
          >
            <span aria-hidden="true">?</span>
            <span>Company Policies</span>
          </NavLink>
        </div>

        <div className="nav-section">
          <h3 className="nav-heading">
            Departments
          </h3>

          <NavLink
            to="/hr"
            className={linkClass}
          >
            <span aria-hidden="true">?</span>
            <span>HR &amp; People</span>
          </NavLink>

          <NavLink
            to="/finance"
            className={linkClass}
          >
            <span aria-hidden="true">?</span>
            <span>Finance</span>
          </NavLink>

          <NavLink
            to="/it-support"
            className={linkClass}
          >
            <span aria-hidden="true">?</span>
            <span>IT Support</span>
          </NavLink>
        </div>

        <div className="nav-section">
          <h3 className="nav-heading">
            Account
          </h3>

          <NavLink
            to="/sessions"
            className={linkClass}
          >
            <span aria-hidden="true">?</span>
            <span>My Sessions</span>
          </NavLink>

          <button
            className="nav-link sidebar-logout"
            type="button"
            onClick={handleLogout}
          >
            <span aria-hidden="true">?</span>
            <span>Logout</span>
          </button>

          {isAdmin && (
            <NavLink
              to="/resources/admin"
              className={linkClass}
            >
              <span aria-hidden="true">?</span>
              <span>Admin Controls</span>
            </NavLink>
          )}
        </div>
      </nav>
    </aside>
  );
};

export default Sidebar;
