import React, { useState, useEffect } from "react";
import socService from "../../services/socService";
import "../dashboard/Dashboard.css";
import { formatDateIST } from "../../utils/dateUtils";

const SocAccessEvents = () => {
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    socService.getAccessHistory().then(setEvents).finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="dashboard-container">Loading Access Events...</div>;

  return (
    <div className="dashboard-container">
      <h1>Access Events</h1>
      {events.length === 0 ? <p>No access events found.</p> : (
        <table className="data-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Time</th>
              <th>Username</th>
              <th>Resource</th>
              <th>IP</th>
              <th>RF High-Risk Probability</th>
              <th>Mismatch</th>
              <th>Decision</th>
            </tr>
          </thead>
          <tbody>
            {events.map(e => (
              <tr key={e.event_id}>
                <td>{e.event_id}</td>
                <td>{formatDateIST(e.timestamp)}</td>
                <td>{e.username}</td>
                <td>{e.resource}</td>
                <td>{e.ip_address}</td>
                <td>{ e.risk_score !== null && e.risk_score !== undefined ? Number(e.risk_score * 100).toFixed(2) + "%" : "-" }</td>
                <td>{e.privilege_mismatch ? "Yes" : "No"}</td>
                <td style={{fontWeight:"bold", color: e.decision === "Allow" ? "green" : (e.decision==="OTP"?"orange":"red")}}>{e.decision}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
};
export default SocAccessEvents;
