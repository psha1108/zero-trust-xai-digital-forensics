import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';
import AdminRoute from './components/AdminRoute';
import Login from './pages/auth/Login';
import Register from './pages/auth/Register';
import DashboardLayout from './components/layout/DashboardLayout';
import Dashboard from './pages/dashboard/Dashboard';
import Profile from './pages/dashboard/Profile';
import NormalResource from './pages/resources/NormalResource';
import HrResource from './pages/resources/HrResource';
import FinanceResource from './pages/resources/FinanceResource';
import AdminResource from './pages/resources/AdminResource';
import ForensicsDashboard from './pages/forensics/ForensicsDashboard';
import EvidenceLogView from './pages/forensics/EvidenceLogView';
import TimelineView from './pages/forensics/TimelineView';
import ForensicReport from './pages/forensics/ForensicReport';
import './index.css'; // Standard CSS

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
              <Route path="/dashboard" element={<Dashboard />} />
              <Route path="/profile" element={<Profile />} />
              <Route path="/resources/normal" element={<NormalResource />} />
              <Route path="/resources/hr" element={<HrResource />} />
              <Route path="/resources/finance" element={<FinanceResource />} />
              <Route path="/resources/admin" element={<AdminResource />} />
              
              {/* Forensics Routes - admin navigation guard */}
              <Route element={<AdminRoute />}>
                <Route path="/forensics" element={<ForensicsDashboard />} />
                <Route path="/forensics/evidence" element={<EvidenceLogView />} />
                <Route path="/forensics/timeline/:sessionId" element={<TimelineView />} />
                <Route path="/forensics/report/:sessionId" element={<ForensicReport />} />
              </Route>
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
