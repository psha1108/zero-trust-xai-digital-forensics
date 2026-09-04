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
          <h3 className="nav-heading">OVERVIEW</h3>
          <NavLink to="/security/overview" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>Security Overview</NavLink>
          <NavLink to="/security/events" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>Security Events</NavLink>
          <NavLink to="/security/sessions" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>Active Sessions</NavLink>
        </div>

        <div className="nav-section">
          <h3 className="nav-heading">MONITORING</h3>
          <NavLink to="/security/login-activity" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>Login Activity</NavLink>
          <NavLink to="/security/access-events" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>Access Events</NavLink>
          <NavLink to="/security/user-sessions" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>User Sessions</NavLink>
        </div>

        <div className="nav-section">
          <h3 className="nav-heading">AI SECURITY</h3>
          <NavLink to="/security/risk-ml" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>Risk & ML Analytics</NavLink>
          <NavLink to="/security/shap" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>SHAP / XAI</NavLink>
        </div>

        <div className="nav-section">
          <h3 className="nav-heading">ZERO TRUST</h3>
          <NavLink to="/security/policy-decisions" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>Policy Decisions</NavLink>
        </div>

        <div className="nav-section">
          <h3 className="nav-heading">DIGITAL FORENSICS</h3>
          {user && user.role === 'admin' ? (
            <>
              <NavLink to="/forensics" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`} end>Evidence</NavLink>
              {/* Other forensic pages are accessed through deep links from the dashboard, but we keep Evidence as the entry point */}
            </>
          ) : (
            <button className="nav-link disabled" title="Admin only" disabled>Digital Forensics</button>
          )}
        </div>
      </nav>
    </aside>
  );
};

export default Sidebar;
