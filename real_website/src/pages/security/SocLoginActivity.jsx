import React, { useState, useEffect } from "react";
import socService from "../../services/socService";
import "../dashboard/Dashboard.css";
import { formatDateIST } from "../../utils/dateUtils";

const SocLoginActivity = () => {
  const [logins, setLogins] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    socService.getLoginHistory().then(setLogins).finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="dashboard-container">Loading Login Activity...</div>;

  return (
    <div className="dashboard-container">
      <h1>Login Activity</h1>
      {logins.length === 0 ? <p>No login activity found.</p> : (
        <table className="data-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Time</th>
              <th>Username</th>
              <th>Success</th>
              <th>IP</th>
              <th>Anomaly Score</th>
              <th>Risk Label</th>
            </tr>
          </thead>
          <tbody>
            {logins.map(l => (
              <tr key={l.event_id}>
                <td>{l.event_id}</td>
                <td>{formatDateIST(l.timestamp)}</td>
                <td>{l.username}</td>
                <td style={{color: l.success ? "green" : "red"}}>{l.success ? "Success" : "Failed"}</td>
                <td>{l.ip_address}</td>
                <td>{l.anomaly_score ?? "-"}</td>
                <td>{l.risk_label ?? "-"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
};
export default SocLoginActivity;
