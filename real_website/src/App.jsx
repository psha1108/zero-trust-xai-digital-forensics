import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';
import Login from './pages/auth/Login';
import Register from './pages/auth/Register';
import DashboardLayout from './components/layout/DashboardLayout';
import Profile from './pages/dashboard/Profile';
import ForensicsDashboard from './pages/forensics/ForensicsDashboard';
import EvidenceLogView from './pages/forensics/EvidenceLogView';
import TimelineView from './pages/forensics/TimelineView';
import ForensicReport from './pages/forensics/ForensicReport';
import UnavailablePage from './pages/security/UnavailablePage';
import './index.css';

const NotFound = () => <div>404 - Not Found</div>;

function App() {
  return (
    <AuthProvider>
      <Router>
        <Routes>
          {/* Public Routes */}
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/" element={<Navigate to="/login" replace />} />
          
          {/* Protected Routes inside DashboardLayout */}
          <Route element={<ProtectedRoute />}>
            <Route element={<DashboardLayout />}>
              <Route path="/dashboard" element={<Navigate to="/security/overview" replace />} />
              <Route path="/profile" element={<Profile />} />
              
              {/* SOC Routes */}
              <Route path="/security/overview" element={<UnavailablePage title="Security Overview" message="A centralized dashboard requires an organization-wide overview API." />} />
              <Route path="/security/events" element={<UnavailablePage title="Security Events" message="Centralized security event aggregation requires a dedicated admin events API." />} />
              <Route path="/security/sessions" element={<UnavailablePage title="Active Sessions" message="Organization-wide session monitoring requires a dedicated admin sessions API." />} />
              
              <Route path="/security/login-activity" element={<UnavailablePage title="Login Activity" message="Organization-wide login activity requires a dedicated admin API." />} />
              <Route path="/security/access-events" element={<UnavailablePage title="Access Events" message="Organization-wide access event monitoring requires a dedicated admin API." />} />
              <Route path="/security/user-sessions" element={<UnavailablePage title="User Sessions" message="Organization-wide user session monitoring requires a dedicated admin API." />} />
              
              <Route path="/security/risk-ml" element={<UnavailablePage title="Risk & ML Analytics" message="Organization-wide ML and Risk metrics require a dedicated admin API." />} />
              <Route path="/security/shap" element={<UnavailablePage title="SHAP / XAI" message="Organization-wide SHAP explanations require a dedicated admin API." />} />
              
              <Route path="/security/policy-decisions" element={<UnavailablePage title="Policy Decisions" message="Organization-wide Zero Trust policy decision monitoring requires a dedicated admin API." />} />

              {/* Forensics Routes - Fully Functional */}
              <Route path="/forensics" element={<ForensicsDashboard />} />
              <Route path="/forensics/evidence" element={<EvidenceLogView />} />
              <Route path="/forensics/timeline/:sessionId" element={<TimelineView />} />
              <Route path="/forensics/report/:sessionId" element={<ForensicReport />} />
            </Route>
          </Route>

          {/* Catch all */}
          <Route path="*" element={<NotFound />} />
        </Routes>
      </Router>
    </AuthProvider>
  );
}

export default App;
