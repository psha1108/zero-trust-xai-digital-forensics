import React, { useState, useEffect } from "react";
import socService from "../../services/socService";
import "../dashboard/Dashboard.css";
import { formatDateIST } from "../../utils/dateUtils";

const SocOverview = () => {
  const [state, setState] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [sessions, setSessions] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [stRes, alRes, sessRes] = await Promise.all([
          socService.getSecurityState(),
          socService.getSecurityAlerts(),
          socService.getActiveSessions()
        ]);
        setState(stRes);
        setAlerts(alRes);
        setSessions(sessRes);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  if (loading) return <div className="dashboard-container">Loading Security Overview...</div>;

  return (
    <div className="dashboard-container">
      <h1>Security Overview</h1>
      <div className="dashboard-grid">
        <div className="dashboard-card">
          <h2>Global Security State</h2>
          {state ? (
            <div>
              <p><strong>Latest RF High-Risk Probability:</strong> {state.risk_score !== null && state.risk_score !== undefined ? Number(state.risk_score * 100).toFixed(2) + "%" : "Not available"}</p>
              <p><strong>Latest Risk Label:</strong> {state.risk_label}</p>
              <p><strong>Active Sessions:</strong> {sessions.length}</p>
            </div>
          ) : <p>Not available</p>}
        </div>
        <div className="dashboard-card" style={{gridColumn: "span 2"}}>
          <h2>Recent Security Alerts</h2>
          {alerts.length === 0 ? <p>No recent alerts.</p> : (
            <table className="data-table">
              <thead><tr><th>Time</th><th>User</th><th>Alert</th><th>Severity</th></tr></thead>
              <tbody>
                {alerts.slice(0,5).map(a => (
                  <tr key={a.event_id}>
                    <td>{formatDateIST(a.timestamp)}</td>
                    <td>{a.username}</td>
                    <td>{a.message}</td>
                    <td style={{color: a.severity === "critical" ? "red" : (a.severity === "high" ? "orange" : "yellow")}}>{a.severity}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  );
};
export default SocOverview;
