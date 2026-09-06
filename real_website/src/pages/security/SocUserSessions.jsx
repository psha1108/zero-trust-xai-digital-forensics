import React, { useState, useEffect } from "react";
import socService from "../../services/socService";
import "../dashboard/Dashboard.css";
import { formatDateIST } from "../../utils/dateUtils";

const SocUserSessions = () => {
  const [sessions, setSessions] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    socService.getSessionsHistory().then(setSessions).finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="dashboard-container">Loading User Sessions...</div>;

  return (
    <div className="dashboard-container">
      <h1>User Sessions (History)</h1>
      {sessions.length === 0 ? <p>No historical sessions found.</p> : (
        <table className="data-table">
          <thead>
            <tr>
              <th>Session ID</th>
              <th>Username</th>
              <th>Started At</th>
              <th>Ended At</th>
              <th>Active</th>
              <th>End Reason</th>
            </tr>
          </thead>
          <tbody>
            {sessions.map(s => (
              <tr key={s.session_id}>
                <td style={{fontFamily:"monospace"}}>{s.session_id.substring(0,8)}...</td>
                <td>{s.username}</td>
                <td>{formatDateIST(s.started_at)}</td>
                <td>{s.ended_at ? formatDateIST(s.ended_at) : "-"}</td>
                <td>{s.is_active ? "Yes" : "No"}</td>
                <td>{s.end_reason || "-"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
};
export default SocUserSessions;
