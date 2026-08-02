import React from 'react';
import { Outlet } from 'react-router-dom';
import Navbar from './Navbar';
import Sidebar from './Sidebar';
import './Layout.css';

const DashboardLayout = () => {
  return (
    <div className="layout-container">
      <Navbar />
      <div className="layout-main">
        <Sidebar />
        <main className="layout-content">
          <Outlet />
        </main>
      </div>
    </div>
  );
};

export default DashboardLayout;
