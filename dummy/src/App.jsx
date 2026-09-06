import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';
import AdminRoute from './components/ProtectedRoute';
import OtpVerificationModal from './components/auth/OtpVerificationModal';

import Login from './pages/auth/Login';
import Register from './pages/auth/Register';
import DashboardLayout from './components/layout/DashboardLayout';
import Dashboard from './pages/dashboard/Dashboard';
import Profile from './pages/dashboard/Profile';

import NormalResource from './pages/resources/NormalResource';
import Tasks from './pages/resources/Tasks';
import Announcements from './pages/resources/Announcements';
import Policies from './pages/resources/Policies';
import ManagementReportsResource from './pages/resources/ManagementReportsResource';

import HrResource from './pages/resources/HrResource';
import FinanceResource from './pages/resources/FinanceResource';
import ItSupport from './pages/resources/ItSupport';

import AdminResource from './pages/resources/AdminResource';
import MySessions from './pages/resources/MySessions';

import './index.css'; // Standard CSS

const NotFound = () => <div>404 - Not Found</div>;

function App() {
  return (
    <AuthProvider>
      <Router>

        {/* OTP verification modal */}
        <OtpVerificationModal />

        <Routes>
          {/* Public Routes */}
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/" element={<Navigate to="/login" replace />} />

          {/* Protected Routes inside DashboardLayout */}
          <Route element={<ProtectedRoute />}>
            <Route element={<DashboardLayout />}>

              {/* Main */}
              <Route path="/dashboard" element={<Dashboard />} />
              <Route path="/profile" element={<Profile />} />

              {/* Workspace */}
              <Route path="/resources/normal" element={<NormalResource />} />
              <Route path="/resources/tasks" element={<Tasks />} />
              <Route path="/resources/announcements" element={<Announcements />} />
              <Route path="/resources/policies" element={<Policies />} />
              <Route
                path="/resources/management-reports"
                element={<ManagementReportsResource />}
              />

              {/* Departments */}
              <Route path="/resources/hr" element={<HrResource />} />
              <Route path="/resources/finance" element={<FinanceResource />} />
              <Route path="/resources/it-support" element={<ItSupport />} />

              {/* Account */}
              <Route path="/resources/my-sessions" element={<MySessions />} />

              {/* Existing Admin Resource */}
              <Route path="/resources/admin" element={<AdminResource />} />

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