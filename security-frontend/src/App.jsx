import React from 'react';
import {
  BrowserRouter as Router,
  Routes,
  Route,
  Navigate,
} from 'react-router-dom';

import { AuthProvider } from './context/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';
import AdminRoute from './components/AdminRoute';

import Login from './pages/auth/Login';
import DashboardLayout from './components/layout/DashboardLayout';
import Dashboard from './pages/dashboard/Dashboard';

import ForensicsDashboard from './pages/forensics/ForensicsDashboard';
import EvidenceLogView from './pages/forensics/EvidenceLogView';
import TimelineView from './pages/forensics/TimelineView';
import ForensicReport from './pages/forensics/ForensicReport';

import './index.css';

const NotFound = () => (
  <div style={{ padding: '2rem' }}>
    404 - Security Console Page Not Found
  </div>
);

function App() {
  return (
    <AuthProvider>
      <Router>
        <Routes>
          <Route
            path="/login"
            element={<Login />}
          />

          <Route
            path="/"
            element={
              <Navigate
                to="/login"
                replace
              />
            }
          />

          <Route element={<ProtectedRoute />}>
            <Route element={<DashboardLayout />}>
              <Route element={<AdminRoute />}>
                <Route
                  path="/dashboard"
                  element={<Dashboard />}
                />

                <Route
                  path="/forensics"
                  element={<ForensicsDashboard />}
                />

                <Route
                  path="/forensics/evidence"
                  element={<EvidenceLogView />}
                />

                <Route
                  path="/forensics/timeline/:sessionId"
                  element={<TimelineView />}
                />

                <Route
                  path="/forensics/report/:sessionId"
                  element={<ForensicReport />}
                />
              </Route>
            </Route>
          </Route>

          <Route
            path="*"
            element={<NotFound />}
          />
        </Routes>
      </Router>
    </AuthProvider>
  );
}

export default App;
