import React, { useState, useEffect } from "react";
import socService from "../../services/socService";
import "../dashboard/Dashboard.css";
import { formatDateIST } from "../../utils/dateUtils";

const SocActiveSessions = () => {
  const [sessions, setSessions] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    socService.getActiveSessions().then(setSessions).finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="dashboard-container">Loading Active Sessions...</div>;

  return (
    <div className="dashboard-container">
      <h1>Active Sessions</h1>
      {sessions.length === 0 ? <p>No active sessions found.</p> : (
        <table className="data-table">
          <thead>
            <tr>
              <th>Session ID</th>
              <th>Username</th>
              <th>Started At</th>
              <th>IP</th>
              <th>RF High-Risk Probability</th>
              <th>Risk Label</th>
            </tr>
          </thead>
          <tbody>
            {sessions.map(s => (
              <tr key={s.session_id}>
                <td style={{fontFamily:"monospace"}}>{s.session_id.substring(0,8)}...</td>
                <td>{s.username}</td>
                <td>{formatDateIST(s.started_at)}</td>
                <td>{s.current_ip}</td>
                <td>{ s.risk_score !== null && s.risk_score !== undefined ? Number(s.risk_score * 100).toFixed(2) + "%" : "-" }</td>
                <td>{s.risk_label ?? "-"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
};
export default SocActiveSessions;
