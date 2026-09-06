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
import SocOverview from './pages/security/SocOverview';
import SocSecurityEvents from './pages/security/SocSecurityEvents';
import SocActiveSessions from './pages/security/SocActiveSessions';
import SocLoginActivity from './pages/security/SocLoginActivity';
import SocAccessEvents from './pages/security/SocAccessEvents';
import SocUserSessions from './pages/security/SocUserSessions';
import SocRiskAnalytics from './pages/security/SocRiskAnalytics';
import SocShap from './pages/security/SocShap';
import SocPolicyDecisions from './pages/security/SocPolicyDecisions';
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
              <Route path="/security/overview" element={<SocOverview />} />
              <Route path="/security/events" element={<SocSecurityEvents />} />
              <Route path="/security/sessions" element={<SocActiveSessions />} />
              
              <Route path="/security/login-activity" element={<SocLoginActivity />} />
              <Route path="/security/access-events" element={<SocAccessEvents />} />
              <Route path="/security/user-sessions" element={<SocUserSessions />} />
              
              <Route path="/security/risk-ml" element={<SocRiskAnalytics />} />
              <Route path="/security/shap" element={<SocShap />} />
              
              <Route path="/security/policy-decisions" element={<SocPolicyDecisions />} />

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
