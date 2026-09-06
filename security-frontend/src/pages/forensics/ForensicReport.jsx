import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import forensicsService from '../../services/forensicsService';
import { formatDateIST } from '../../utils/dateUtils';
import './Forensics.css';

const ForensicReport = () => {
  const { sessionId } = useParams();
  const navigate = useNavigate();
  const [report, setReport] = useState(null);
  const [integrityStatus, setIntegrityStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchReportData = async () => {
      try {
        const reportData = await forensicsService.getReport(sessionId);
        setReport(reportData);
        
        try {
          const verifyData = await forensicsService.verifyIntegrity();
          setIntegrityStatus(verifyData);
        } catch (vErr) {
          setIntegrityStatus({ status: 'ERROR', reason: 'Verification failed' });
        }
      } catch (err) {
        if (err.response?.status === 404) {
          setError('Session not found.');
        } else if (err.response?.status === 403) {
          setError('Forbidden: Admin access required.');
        } else {
          setError(err.response?.data?.error || 'Failed to fetch report');
        }
      } finally {
        setLoading(false);
      }
    };
    fetchReportData();
  }, [sessionId]);

  if (loading) return <div className="forensics-container">Loading report data...</div>;
  if (error) return <div className="forensics-container" style={{ color: 'red' }}>Error: {error}</div>;
  if (!report) return null;

  return (
    <div style={{ padding: '20px' }} className="printable-report-container">
      <div className="no-print" style={{ marginBottom: '20px' }}>
        <button className="forensics-btn" onClick={() => navigate(`/forensics/timeline/${sessionId}`)} style={{ marginRight: '10px' }}>Back to Timeline</button>
        <button className="forensics-btn primary" onClick={() => window.print()}>Print / Export PDF</button>
      </div>

      <div className="report-document">
        <div className="report-header" style={{ textAlign: 'center', marginBottom: '30px' }}>
          <h1 style={{ border: 'none', margin: '0' }}>DIGITAL FORENSIC INVESTIGATION REPORT</h1>
          <h3 style={{ margin: '5px 0' }}>Zero Trust Security Dashboard</h3>
          <p style={{ fontWeight: 'bold' }}>CONFIDENTIAL</p>
        </div>

        <h2>1. REPORT IDENTIFICATION</h2>
        <div className="meta-info">
          <p><strong>Report ID:</strong> {report.report_identification.report_id}</p>
          <p><strong>Report Version:</strong> 1.0</p>
          <p><strong>Report Status:</strong> Final</p>
          <p><strong>Generation Time:</strong> {formatDateIST(new Date().toISOString())}</p>
          <p><strong>Affected User ID:</strong> {report.report_identification.user_id}</p>
          <p><strong>Session ID:</strong> {report.report_identification.session_id}</p>
        </div>

        <h2>2. INVESTIGATION REQUEST AND AUTHORITY</h2>
        <div className="meta-info">
          <p><strong>Examiner:</strong> Digital Forensics Administrator</p>
          <p><strong>Organization:</strong> Not specified</p>
        </div>

        <h2>3. INVESTIGATION SCOPE</h2>
        <p>This report covers all recorded security events and corresponding cryptographic evidence chains associated with session ID <strong>{report.report_identification.session_id}</strong>.</p>

        <h2>4. INCIDENT OVERVIEW</h2>
        <div className="meta-info">
          <p><strong>Start Time:</strong> {formatDateIST(report.incident_overview.start_time)}</p>
          <p><strong>End Time:</strong> {report.incident_overview.end_time ? formatDateIST(report.incident_overview.end_time) : 'Ongoing'}</p>
          <p><strong>Session Status:</strong> {report.incident_overview.session_status}</p>
        </div>

        <h2>5. EVIDENCE INVENTORY</h2>
        {report.evidence_inventory.length > 0 ? (
          <table className="evidence-table">
            <thead>
              <tr>
                <th>Evidence ID</th>
                <th>Event ID</th>
                <th>Event Type</th>
                <th>Timestamp</th>
                <th>Record Hash</th>
                <th>Previous Hash</th>
              </tr>
            </thead>
            <tbody>
              {report.evidence_inventory.map(ev => {
                const eId = ev.details?.event?.event_id || (ev.details?.event_type === 'LoginEvent' ? ev.details?.login_event_id : (ev.details?.event_type === 'AccessEvent' ? ev.details?.access_event_id : null)) || 'Unknown';
                const eType = ev.details?.event?.event_type || ev.details?.event_type || 'Unknown';
                return (
                  <tr key={ev.evidence_id}>
                    <td>{ev.evidence_id}</td>
                    <td>{eId}</td>
                    <td>{eType}</td>
                    <td>{formatDateIST(ev.timestamp)}</td>
                    <td className="hash-text">{ev.record_hash || 'Not available'}</td>
                    <td className="hash-text">{ev.previous_hash || 'Not available'}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        ) : (
          <p>No evidence logs preserved for this session.</p>
        )}

        <h2>6. EVIDENCE PRESERVATION AND INTEGRITY</h2>
        <p>This project investigates application-generated digital evidence. No physical device seizure is claimed. Evidence provenance is established through evidence identifiers, timestamps, session correlation, authenticated access, cryptographic hashes, and the evidence integrity chain.</p>
        <p>Evidence is preserved using a deterministic JSON serialization of the event payload, securely hashed via SHA-256 and cryptographically chained to the preceding evidence record to prevent retroactive tampering.</p>

        <h2>7. INCIDENT TIMELINE</h2>
        <table>
          <thead>
            <tr>
              <th>Timestamp</th>
              <th>Action</th>
              <th>IP Address</th>
            </tr>
          </thead>
          <tbody>
            {report.incident_timeline.map((event, i) => (
              <tr key={i}>
                <td>{formatDateIST(event.timestamp)}</td>
                <td>{event.action}</td>
                <td>{event.ip_address}</td>
              </tr>
            ))}
          </tbody>
        </table>

        <h2>8. ML / RISK ANALYSIS</h2>
        {report.evidence_inventory.some(ev => ev.details?.ml) ? (
          <ul>
            {report.evidence_inventory.filter(ev => ev.details?.ml).map((ev, i) => {
              const ml = ev.details.ml;
              const iforest = ml.isolation_forest || {};
              const rforest = ml.random_forest || {};
              const kmeans = ml.kmeans || {};
              return (
                <li key={i}>
                  [{formatDateIST(ev.timestamp)}] Event ID {ev.details?.event?.event_id || 'Unknown'} - 
                  IF Anomaly: {iforest.anomaly_score ?? 'N/A'}, 
                  RF Risk: {rforest.risk_label || 'N/A'} (Score: {rforest.risk_score ?? 'N/A'}), 
                  Cluster: {kmeans.cluster_id ?? 'N/A'}
                </li>
              );
            })}
          </ul>
        ) : (
          <p>Risk Assessment: Not available</p>
        )}

        <h2>9. SHAP EXPLANATION</h2>
        {report.evidence_inventory.some(ev => (ev.details?.shap && Object.keys(ev.details.shap).length > 0) || (ev.details?.xai?.shap && Object.keys(ev.details.xai.shap).length > 0)) ? (
          <div>
            {report.evidence_inventory.filter(ev => (ev.details?.shap && Object.keys(ev.details.shap).length > 0) || (ev.details?.xai?.shap && Object.keys(ev.details.xai.shap).length > 0)).map((ev, i) => {
              const shapData = ev.details.shap || ev.details.xai.shap;
              return (
              <div key={i} style={{ marginBottom: '15px' }}>
                <p><strong>Event ID {ev.details?.event?.event_id || 'Unknown'}</strong> ({formatDateIST(ev.timestamp)}):</p>
                <table className="shap-table" style={{ width: '100%', borderCollapse: 'collapse' }}>
                  <thead>
                    <tr>
                      <th style={{ border: '1px solid #ccc', padding: '5px' }}>Feature</th>
                      <th style={{ border: '1px solid #ccc', padding: '5px' }}>Value</th>
                      <th style={{ border: '1px solid #ccc', padding: '5px' }}>Contribution</th>
                    </tr>
                  </thead>
                  <tbody>
                    {Object.entries(shapData).map(([feature, data]) => (
                      <tr key={feature}>
                        <td style={{ border: '1px solid #ccc', padding: '5px' }}>{feature}</td>
                        <td style={{ border: '1px solid #ccc', padding: '5px' }}>{data.value !== undefined ? data.value : 'N/A'}</td>
                        <td style={{ border: '1px solid #ccc', padding: '5px' }}>{data.contribution !== undefined ? data.contribution.toFixed(4) : 'N/A'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )})}
          </div>
        ) : (
          <p>SHAP Explanation: Not available</p>
        )}

        <h2>10. ZERO TRUST / ACCESS CONTROL ANALYSIS</h2>
        <ul>
          {report.incident_timeline.map((e, i) => (
            <li key={i}>[{formatDateIST(e.timestamp)}] {e.action}: <strong>Decision: {e.result ? e.result.toUpperCase() : 'NOT AVAILABLE'}</strong></li>
          ))}
        </ul>

        <h2>11. INVESTIGATION FINDINGS</h2>
        <ul>
          <li>Total Access Events: {report.investigation_findings.total_access_events}</li>
          <li>Blocked/Denied Accesses: {report.investigation_findings.blocked_access_events}</li>
          <li>Privilege Mismatches: {report.investigation_findings.privilege_mismatches}</li>
        </ul>

        <h2>12. INTEGRITY VERIFICATION RESULT</h2>
        <p>
          <strong>Status: </strong> 
          {integrityStatus ? (
            <span style={{ fontWeight: 'bold', color: integrityStatus.status === 'VALID' ? 'green' : 'red' }}>
              {integrityStatus.status}
            </span>
          ) : 'Pending...'}
        </p>
        
        <h2>13. EVIDENCE HANDLING, PROVENANCE AND DISPOSITION</h2>
        <div className="meta-info">
          <p><strong>Source:</strong> Generated by the application</p>
          <p><strong>Storage / Repository:</strong> Preserved in the forensic evidence log</p>
          <p><strong>Analysis Status:</strong> Verified using SHA-256 hash-chain validation</p>
          <p><strong>Disposition:</strong> Retained securely in database</p>
        </div>

      </div>
    </div>
  );
};

export default ForensicReport;
