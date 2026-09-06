import React, { useState, useEffect } from "react";
import socService from "../../services/socService";
import "../dashboard/Dashboard.css";
import { formatDateIST } from "../../utils/dateUtils";

const SocSecurityEvents = () => {
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    socService.getSecurityAlerts().then(setEvents).finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="dashboard-container">Loading Security Events...</div>;

  return (
    <div className="dashboard-container">
      <h1>Security Events</h1>
      {events.length === 0 ? <p>No security events found.</p> : (
        <table className="data-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Time</th>
              <th>User</th>
              <th>Type</th>
              <th>Resource</th>
              <th>Policy Action</th>
              <th>Severity</th>
            </tr>
          </thead>
          <tbody>
            {events.map(e => (
              <tr key={e.event_id}>
                <td>{e.event_id}</td>
                <td>{formatDateIST(e.timestamp)}</td>
                <td>{e.username}</td>
                <td>{e.alert_type}</td>
                <td>{e.resource || "-"}</td>
                <td>{e.policy_action}</td>
                <td style={{color: e.severity === "critical" ? "red" : (e.severity === "high" ? "orange" : "yellow")}}>{e.severity}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
};
export default SocSecurityEvents;
