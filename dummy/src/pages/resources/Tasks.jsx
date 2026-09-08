import React, { useState } from 'react';
import Card from '../../components/dashboard/Card';
import { TASKS } from '../../data/tasks';

const Tasks = () => {
  const [selectedTask, setSelectedTask] = useState(null);

  if (selectedTask) {
    return (
      <div className="resource-view-container">
        <button className="resource-btn-back" onClick={() => setSelectedTask(null)}>
          &larr; BACK TO TASKS
        </button>
        <Card>
          <div style={{ padding: '20px' }}>
            <h2 style={{ marginTop: 0, marginBottom: '10px', color: 'var(--primary-color)' }}>{selectedTask.title}</h2>
            <div style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', marginBottom: '20px', display: 'flex', gap: '15px', flexWrap: 'wrap' }}>
              <span><strong>Task ID:</strong> {selectedTask.id}</span>
              <span>
                <strong>Priority:</strong>
                <span style={{
                  marginLeft: '5px',
                  padding: '2px 6px',
                  borderRadius: '10px',
                  backgroundColor: selectedTask.priority === 'High' ? '#fee2e2' : '#e0f2fe',
                  color: selectedTask.priority === 'High' ? '#991b1b' : '#0369a1',
                  fontSize: '0.85em'
                }}>
                  {selectedTask.priority}
                </span>
              </span>
              <span><strong>Status:</strong> {selectedTask.status}</span>
              <span><strong>Due Date:</strong> {selectedTask.due}</span>
              <span><strong>Category:</strong> {selectedTask.category}</span>
            </div>
            
            <div style={{ borderTop: '1px solid var(--border-color)', paddingTop: '20px', marginBottom: '20px' }}>
              <h3 style={{ marginTop: 0, marginBottom: '10px' }}>Task Description</h3>
              <p style={{ lineHeight: '1.6' }}>{selectedTask.description}</p>
            </div>

            <div style={{ borderTop: '1px solid var(--border-color)', paddingTop: '20px', marginBottom: '20px' }}>
              <h3 style={{ marginTop: 0, marginBottom: '10px' }}>Details / Checklist</h3>
              <ul style={{ lineHeight: '1.6', paddingLeft: '20px' }}>
                {selectedTask.checklist.map((item, idx) => (
                  <li key={idx}>{item}</li>
                ))}
              </ul>
            </div>

            <div style={{ borderTop: '1px solid var(--border-color)', paddingTop: '20px' }}>
              <h3 style={{ marginTop: 0, marginBottom: '10px' }}>Current Progress</h3>
              <p style={{ fontWeight: '600', color: selectedTask.progress.includes('Not Started') || selectedTask.progress.includes('Pending') || selectedTask.progress.includes('Not Submitted') ? '#d97706' : '#0284c7' }}>
                {selectedTask.progress}
              </p>
            </div>
          </div>
        </Card>
      </div>
    );
  }

  return (
    <div className="resource-view-container">
      <h1 className="page-title">My Tasks</h1>
      <p style={{ color: 'var(--text-secondary)', marginBottom: '24px' }}>Track assigned tasks, deadlines, priorities, and current progress.</p>

      <div className="resource-grid">
        {TASKS.map(task => (
          <div key={task.id} className="resource-card-container">
            <Card className="resource-card-content">
              <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '15px' }}>
                  <h3 style={{ margin: 0, fontSize: '1.1em', paddingRight: '10px' }}>{task.title}</h3>
                  <span style={{
                    fontSize: '0.8em',
                    padding: '3px 8px',
                    borderRadius: '12px',
                    backgroundColor: task.priority === 'High' ? '#fee2e2' : '#e0f2fe',
                    color: task.priority === 'High' ? '#991b1b' : '#0369a1',
                    whiteSpace: 'nowrap'
                  }}>
                    {task.priority}
                  </span>
                </div>

                <p style={{ fontSize: '0.9em', color: 'var(--text-secondary)', marginBottom: '20px', flexGrow: 1 }}>
                  {task.description.length > 100 ? task.description.substring(0, 100) + '...' : task.description}
                </p>

                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.9em', color: 'var(--text-secondary)', marginBottom: '10px' }}>
                  <span><strong>Due:</strong> {task.due}</span>
                  <span style={{ fontWeight: 'bold', color: task.status === 'Pending' ? '#d97706' : '#0284c7' }}>
                    {task.status}
                  </span>
                </div>
                
                <div style={{ fontSize: '0.8em', color: '#999', borderTop: '1px solid var(--border-color)', paddingTop: '10px', marginTop: '10px' }}>
                  Task ID: {task.id}
                </div>
                <button className="resource-btn" onClick={() => setSelectedTask(task)}>VIEW</button>
              </div>
            </Card>
          </div>
        ))}
      </div>
    </div>
  );
};

export default Tasks;
