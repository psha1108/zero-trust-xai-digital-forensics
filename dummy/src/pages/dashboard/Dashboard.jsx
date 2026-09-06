import React from 'react';
import Card from '../../components/dashboard/Card';
import SessionStatusCard from '../../components/dashboard/SessionStatusCard';
import './Dashboard.css';

import { CURRENT_EMPLOYEE } from '../../data/employees';
import { TASKS } from '../../data/tasks';
import { ANNOUNCEMENTS } from '../../data/announcements';

const Dashboard = () => {
  const openTasks = TASKS.filter(t => t.status !== 'Resolved').length;
  const unreadAnnouncements = ANNOUNCEMENTS.length;

  return (
    <div className="dashboard-container">
      <h1 className="page-title">Welcome back, {CURRENT_EMPLOYEE.name.split(' ')[0]}.</h1>
      
      <div style={{ marginBottom: '20px' }}>
        <h3 style={{ margin: '0' }}>{CURRENT_EMPLOYEE.department}</h3>
        <p style={{ margin: '0', color: '#555' }}>{CURRENT_EMPLOYEE.designation}</p>
      </div>

      <div className="dashboard-grid">
        <Card title="Summary">
          <ul style={{ listStyleType: 'none', padding: 0 }}>
            <li style={{ padding: '8px 0', borderBottom: '1px solid #eee' }}>Open Tasks: {openTasks}</li>
            <li style={{ padding: '8px 0', borderBottom: '1px solid #eee' }}>Pending Requests: 2</li>
            <li style={{ padding: '8px 0', borderBottom: '1px solid #eee' }}>Unread Announcements: {unreadAnnouncements}</li>
            <li style={{ padding: '8px 0' }}>Available Documents: 8</li>
          </ul>
        </Card>

        <Card title="Recent Activity">
          <ul style={{ paddingLeft: '20px' }}>
            <li>Viewed Employee Handbook</li>
            <li>Submitted IT Support Request</li>
            <li>Viewed Company Policies</li>
            <li>Updated Profile</li>
          </ul>
        </Card>

        <Card title="Tasks">
          <ul style={{ paddingLeft: '20px' }}>
            {TASKS.map(task => (
              <li key={task.id}>{task.title}</li>
            ))}
          </ul>
        </Card>

        <Card title="Announcements">
          <ul style={{ paddingLeft: '20px' }}>
            {ANNOUNCEMENTS.map(ann => (
              <li key={ann.id}>{ann.title}</li>
            ))}
          </ul>
        </Card>

        <SessionStatusCard />
      </div>
    </div>
  );
};

export default Dashboard;
