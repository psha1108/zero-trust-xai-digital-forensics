import React from 'react';
import { NavLink } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import './Layout.css';

const Sidebar = () => {
  const { user } = useAuth();
  
  return (
    <aside className="sidebar">
      <nav className="sidebar-nav">
        <div className="nav-section">
          <h3 className="nav-heading">Main</h3>
          <NavLink to="/dashboard" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
            Dashboard
          </NavLink>
          <NavLink to="/profile" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
            Profile
          </NavLink>
        </div>

        <div className="nav-section">
          <h3 className="nav-heading">Resources</h3>
          <NavLink to="/resources/normal" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
            Normal Access
          </NavLink>
          <NavLink to="/resources/hr" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
            HR Department
          </NavLink>
          <NavLink to="/resources/finance" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
            Finance Department
          </NavLink>
          <NavLink to="/resources/admin" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
            Admin Controls
          </NavLink>
        </div>

      </nav>
    </aside>
  );
};

export default Sidebar;
