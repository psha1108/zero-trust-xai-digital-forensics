import React from 'react';
import { NavLink } from 'react-router-dom';
import './Layout.css';

const Sidebar = () => {
  const linkClass = ({ isActive }) =>
    `nav-link ${isActive ? 'active' : ''}`;

  return (
    <aside className="sidebar">
      <nav className="sidebar-nav">
        <div className="nav-section">
          <h3 className="nav-heading">
            Portal
          </h3>

          <NavLink
            to="/dashboard"
            className={linkClass}
          >
            Home
          </NavLink>

          <NavLink
            to="/profile"
            className={linkClass}
          >
            My Profile
          </NavLink>
        </div>

        <div className="nav-section">
          <h3 className="nav-heading">
            Resources
          </h3>

          <NavLink
            to="/resources/normal"
            className={linkClass}
          >
            General Documents
          </NavLink>

          <NavLink
            to="/resources/hr"
            className={linkClass}
          >
            HR Documents
          </NavLink>

          <NavLink
            to="/resources/finance"
            className={linkClass}
          >
            Finance Reports
          </NavLink>

          <NavLink
            to="/resources/admin"
            className={linkClass}
          >
            Admin Controls
          </NavLink>
        </div>
      </nav>
    </aside>
  );
};

export default Sidebar;
