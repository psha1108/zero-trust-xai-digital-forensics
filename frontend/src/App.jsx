import React from 'react';
import {
  BrowserRouter as Router,
  Navigate,
  Route,
  Routes,
} from 'react-router-dom';

import { AuthProvider } from './context/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';

import Login from './pages/auth/Login';
import Register from './pages/auth/Register';

import DashboardLayout from './components/layout/DashboardLayout';
import Dashboard from './pages/dashboard/Dashboard';
import Profile from './pages/dashboard/Profile';

import NormalResource from './pages/resources/NormalResource';
import HrResource from './pages/resources/HrResource';
import FinanceResource from './pages/resources/FinanceResource';
import AdminResource from './pages/resources/AdminResource';
import ManagementReportsResource from './pages/resources/ManagementReportsResource';

import Tasks from './pages/portal/Tasks';
import Announcements from './pages/portal/Announcements';
import Policies from './pages/portal/Policies';
import ItSupport from './pages/portal/ItSupport';
import MySessions from './pages/portal/MySessions';

import './index.css';

const NotFound = () => (
  <div style={{ padding: '2rem' }}>
    <h1>Page Not Found</h1>
    <p>
      The requested corporate portal page could not be found.
    </p>
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
            path="/register"
            element={<Register />}
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
              <Route
                path="/dashboard"
                element={<Dashboard />}
              />

              <Route
                path="/profile"
                element={<Profile />}
              />

              <Route
                path="/documents"
                element={<NormalResource />}
              />

              <Route
                path="/tasks"
                element={<Tasks />}
              />

              <Route
                path="/announcements"
                element={<Announcements />}
              />

              <Route
                path="/policies"
                element={<Policies />}
              />

              <Route
                path="/hr"
                element={<HrResource />}
              />

              <Route
                path="/finance"
                element={<FinanceResource />}
              />

              <Route
                path="/it-support"
                element={<ItSupport />}
              />

              <Route
                path="/sessions"
                element={<MySessions />}
              />

              <Route
                path="/resources/management-reports"
                element={<ManagementReportsResource />}
              />

              <Route
                path="/resources/admin"
                element={<AdminResource />}
              />

              {/* Compatibility routes retained for existing links/tests. */}
              <Route
                path="/resources/normal"
                element={
                  <Navigate
                    to="/documents"
                    replace
                  />
                }
              />

              <Route
                path="/resources/hr"
                element={
                  <Navigate
                    to="/hr"
                    replace
                  />
                }
              />

              <Route
                path="/resources/finance"
                element={
                  <Navigate
                    to="/finance"
                    replace
                  />
                }
              />
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
