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
            Security Operations
          </h3>

          <NavLink
            to="/dashboard"
            className={linkClass}
          >
            Security Overview
          </NavLink>
        </div>

        <div className="nav-section">
          <h3 className="nav-heading">
            Investigation
          </h3>

          <NavLink
            to="/forensics"
            className={linkClass}
          >
            Digital Forensics
          </NavLink>
        </div>
      </nav>
    </aside>
  );
};

export default Sidebar;
