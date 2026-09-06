import React from 'react';
import Card from '../../components/dashboard/Card';
import { TASKS } from '../../data/tasks';

const Tasks = () => {
  return (
    <div className="resource-view-container">
      <h1 className="page-title">My Tasks</h1>
      
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '20px' }}>
        {TASKS.map(task => (
          <Card key={task.id}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '15px' }}>
              <h3 style={{ margin: 0, fontSize: '1.1em', paddingRight: '10px' }}>{task.title}</h3>
              <span style={{ 
                fontSize: '0.8em', 
                padding: '3px 8px', 
                borderRadius: '12px',
                backgroundColor: task.priority === 'High' ? '#fee2e2' : '#e0f2fe',
                color: task.priority === 'High' ? '#991b1b' : '#0369a1'
              }}>
                {task.priority}
              </span>
            </div>
            
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.9em', color: '#555', marginTop: 'auto' }}>
              <span><strong>Due:</strong> {task.due}</span>
              <span style={{ fontWeight: 'bold', color: task.status === 'Pending' ? '#d97706' : '#0284c7' }}>
                {task.status}
              </span>
            </div>
            <div style={{ fontSize: '0.8em', color: '#999', marginTop: '10px', borderTop: '1px solid #eee', paddingTop: '5px' }}>
              Task ID: {task.id}
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
};

export default Tasks;
