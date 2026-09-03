import React from 'react';
import { useNavigate } from 'react-router-dom';
import './Forensics.css';

const ForensicsDashboard = () => {
  const navigate = useNavigate();

  return (
    <div className="forensics-container">
      <h1 className="forensics-header">Digital Forensics Dashboard</h1>
      <p>Welcome to the Digital Forensics module. Please select a tool:</p>
      
      <div className="forensics-nav">
        <button className="forensics-btn" onClick={() => navigate('/forensics/evidence')}>
          View Evidence Log
        </button>
      </div>

      <div style={{ marginTop: '30px', padding: '20px', backgroundColor: '#2a2a2a', borderRadius: '4px' }}>
        <h3>Investigate Session</h3>
        <p>Enter a Session ID to view its timeline or generate a report.</p>
        <form onSubmit={(e) => {
          e.preventDefault();
          const sessionId = e.target.elements.sessionId.value.trim();
          if (sessionId) {
            navigate(`/forensics/timeline/${sessionId}`);
          }
        }}>
          <input 
            name="sessionId" 
            placeholder="Session ID..." 
            style={{ padding: '8px', marginRight: '10px', width: '300px' }} 
            required 
          />
          <button type="submit" className="forensics-btn primary">View Timeline</button>
        </form>
      </div>
    </div>
  );
};

export default ForensicsDashboard;
