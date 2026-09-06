import React from 'react';
import { NavLink } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import './Layout.css';

const Sidebar = () => {
  const { user } = useAuth();
  
  return (
    <aside className="sidebar">
      <div className="sidebar-brand">
        <h2>ACME TECHNOLOGIES</h2>
      </div>
      <nav className="sidebar-nav">
        <div className="nav-section">
          <h3 className="nav-heading">Main</h3>
          <NavLink to="/dashboard" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
            Dashboard
          </NavLink>
          <NavLink to="/profile" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
            My Profile
          </NavLink>
        </div>

        <div className="nav-section">
          <h3 className="nav-heading">Workspace</h3>
          <NavLink to="/resources/normal" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
            Documents
          </NavLink>
          <NavLink to="/resources/tasks" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
            My Tasks
          </NavLink>
          <NavLink to="/resources/announcements" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
            Announcements
          </NavLink>
          <NavLink to="/resources/policies" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
            Company Policies
          </NavLink>
          <NavLink to="/resources/management-reports" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
            Management Reports
          </NavLink>
        </div>

        <div className="nav-section">
          <h3 className="nav-heading">Departments</h3>
          <NavLink to="/resources/hr" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
            HR & People
          </NavLink>
          <NavLink to="/resources/finance" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
            Finance
          </NavLink>
          <NavLink to="/resources/it-support" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
            IT Support
          </NavLink>
        </div>
        
        <div className="nav-section">
          <h3 className="nav-heading">Account</h3>
          <NavLink to="/resources/my-sessions" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
            My Sessions
          </NavLink>
          {/* Logout is handled in Navbar currently, placeholder here */}
          <div className="nav-link disabled" style={{opacity: 0.5, cursor: 'not-allowed'}}>Logout</div>
        </div>
      </nav>
    </aside>
  );
};

export default Sidebar;
