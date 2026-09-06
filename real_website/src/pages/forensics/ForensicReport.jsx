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
        <div className="report-header" style={{ textAlign: 'center', marginBottom: '30px', borderBottom: '2px solid black', paddingBottom: '15px' }}>
          <h1 style={{ border: 'none', margin: '0', fontSize: '2em', letterSpacing: '2px' }}>DIGITAL FORENSIC INVESTIGATION REPORT</h1>
          <h3 style={{ margin: '5px 0', fontWeight: 'normal' }}>ACME Security Operations Center - Zero Trust Forensic Division</h3>
          <p style={{ fontWeight: 'bold', color: '#be123c', border: '1px solid #be123c', display: 'inline-block', padding: '2px 8px' }}>CONFIDENTIAL & RESTRICTED</p>
        </div>

        <h2>1. REPORT IDENTIFICATION</h2>
        <table className="meta-table">
          <tbody>
            <tr>
              <td><strong>Report ID:</strong></td><td>{report.report_identification.report_id}</td>
              <td><strong>Report Date:</strong></td><td>{report.report_identification.timestamp ? formatDateIST(report.report_identification.timestamp) : formatDateIST(new Date().toISOString())}</td>
            </tr>
            <tr>
              <td><strong>Target Subject (User ID):</strong></td><td>{report.report_identification.user_id}</td>
              <td><strong>Session Identifier:</strong></td><td>{report.report_identification.session_id}</td>
            </tr>
          </tbody>
        </table>

        <h2>2. EXECUTIVE SUMMARY</h2>
        <div className="meta-info">
          <p>This report documents a digital forensic investigation into session <strong>{report.report_identification.session_id}</strong> associated with user ID <strong>{report.report_identification.user_id}</strong>.</p>
          <p>The investigated session began at <strong>{formatDateIST(report.incident_overview.start_time)}</strong> and concluded at <strong>{report.incident_overview.end_time ? formatDateIST(report.incident_overview.end_time) : 'Ongoing'}</strong>.</p>
          <p>The forensic extraction captured <strong>{report.investigation_findings.total_access_events}</strong> documented access events. The highest enforcement response recorded was <strong>{report.investigation_findings.blocked_access_events > 0 ? "Block" : report.investigation_findings.privilege_mismatches > 0 ? "Restrict" : "Allow"}</strong>.</p>
        </div>

        <h2>3. AUTHORITY AND SCOPE</h2>
        <div className="meta-info">
          <p><strong>Authority:</strong> ACME Zero Trust Security Policy enforcement protocol.</p>
          <p><strong>Examiner:</strong> Digital Forensics Administrator (Automated System Extraction).</p>
          <p><strong>Scope:</strong> Identification, preservation, and analysis of cryptographic evidence chains, machine learning anomaly classifications, explainable AI (SHAP) attributions, and definitive policy enforcement actions for the designated session.</p>
        </div>

        <h2>4. EVIDENCE INVENTORY</h2>
        {report.evidence_inventory.length > 0 ? (
          <table className="evidence-table">
            <thead>
              <tr>
                <th>Ev. ID</th>
                <th>Timestamp</th>
                <th>Event Type</th>
                <th>Record Hash (SHA-256)</th>
                <th>Integrity Link (Prev. Hash)</th>
              </tr>
            </thead>
            <tbody>
              {report.evidence_inventory.map(ev => {
                const eType = ev.details?.event?.event_type || ev.details?.event_type || 'Unknown';
                return (
                  <tr key={ev.evidence_id}>
                    <td>{ev.evidence_id}</td>
                    <td>{formatDateIST(ev.timestamp)}</td>
                    <td>{eType}</td>
                    <td className="hash-text">{ev.record_hash || 'Not available'}</td>
                    <td className="hash-text">{ev.previous_hash || 'Not available'}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        ) : (
          <p>No cryptographic evidence logs preserved for this session.</p>
        )}

        <h2>5. EVIDENCE DETAILS AND PAYLOAD</h2>
        {report.evidence_inventory.length > 0 ? (
          report.evidence_inventory.map((ev, index) => {
            const det = ev.details || {};
            const eType = det.event?.event_type || det.event_type || 'Not available';
            const eTime = det.event?.timestamp || det.timestamp || 'Not available';
            const resource = det.resource?.name || det.resource;
            const ip = det.network?.ip_address || det.ip_address;
            const device = det.device?.device_fingerprint || det.device?.device_info || det.device_fingerprint || det.device_info;
            
            return (
              <div key={index} className="evidence-detail-block">
                <h3>Evidence Record: {ev.evidence_id}</h3>
                <table className="detail-table">
                  <tbody>
                    <tr><td><strong>Event Type:</strong></td><td>{eType}</td></tr>
                    <tr><td><strong>Timestamp:</strong></td><td>{eTime !== 'Not available' ? formatDateIST(eTime) : eTime}</td></tr>
                    {resource && typeof resource === 'string' && <tr><td><strong>Target Resource:</strong></td><td>{resource}</td></tr>}
                    {ip && typeof ip === 'string' && <tr><td><strong>Source IP:</strong></td><td>{ip}</td></tr>}
                    {device && typeof device === 'string' && <tr><td><strong>Device:</strong></td><td>{device}</td></tr>}
                  </tbody>
                </table>
              </div>
            );
          })
        ) : (
          <p>Evidence details not available.</p>
        )}

        <h2>6. ML / RISK ASSESSMENT</h2>
        {report.incident_timeline.some(e => e.risk_label || e.anomaly_score !== null || e.risk_score !== null) ? (
          <table className="evidence-table">
            <thead>
              <tr>
                <th>Timestamp</th>
                <th>Action / Resource</th>
                <th>Risk Label</th>
                <th>RF Probability</th>
                <th>IF Anomaly</th>
                <th>Cluster ID</th>
              </tr>
            </thead>
            <tbody>
              {report.incident_timeline.filter(e => e.risk_label || e.anomaly_score !== null || e.risk_score !== null).map((e, i) => (
                <tr key={i}>
                  <td>{formatDateIST(e.timestamp)}</td>
                  <td>{e.action}</td>
                  <td><strong>{e.risk_label || 'N/A'}</strong></td>
                  <td>{e.risk_score !== null ? (e.risk_score * 100).toFixed(2) + '%' : 'N/A'}</td>
                  <td>{e.anomaly_score !== null ? e.anomaly_score : 'N/A'}</td>
                  <td>{e.cluster_id !== null ? e.cluster_id : 'N/A'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <p>ML Assessment data not available.</p>
        )}

        <h2>7. SHAP / XAI ANALYSIS</h2>
        {report.evidence_inventory.some(ev => ev.details?.shap) ? (
          report.evidence_inventory.filter(ev => ev.details?.shap).map((ev, idx) => {
            const shap = ev.details.shap;
            const explanation = shap.explanation || {};
            const contributions = explanation.contributions || [];
            return (
              <div key={idx} className="shap-block">
                <h3>XAI Analysis for Evidence {ev.evidence_id}</h3>
                <p><strong>Base Value:</strong> {explanation.base_value !== undefined ? explanation.base_value.toFixed(4) : 'N/A'}</p>
                <p><strong>Final Prediction Output:</strong> {shap.prediction !== undefined ? shap.prediction : 'N/A'}</p>
                {contributions.length > 0 && (
                  <table className="evidence-table">
                    <thead>
                      <tr>
                        <th>Feature</th>
                        <th>Contribution Value</th>
                        <th>Impact Direction</th>
                      </tr>
                    </thead>
                    <tbody>
                      {contributions.sort((a, b) => Math.abs(b.contribution) - Math.abs(a.contribution)).map((c, cIdx) => (
                        <tr key={cIdx}>
                          <td>{c.feature_name}</td>
                          <td className="hash-text">{c.contribution.toFixed(6)}</td>
                          <td style={{ color: c.contribution > 0 ? '#b91c1c' : '#15803d', fontWeight: 'bold' }}>
                            {c.contribution > 0 ? 'Positive (Increased Risk)' : 'Negative (Decreased Risk)'}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
              </div>
            );
          })
        ) : (
          <p>SHAP data not available for any evidence records in this session.</p>
        )}

        <h2>8. ZERO TRUST POLICY ANALYSIS</h2>
        <table className="evidence-table">
          <thead>
            <tr>
              <th>Timestamp</th>
              <th>Action</th>
              <th>Enforcement Decision</th>
              <th>Session Impact</th>
            </tr>
          </thead>
          <tbody>
            {report.incident_timeline.map((e, i) => (
              <tr key={i}>
                <td>{formatDateIST(e.timestamp)}</td>
                <td>{e.action}</td>
                <td style={{ fontWeight: 'bold', color: e.result?.toLowerCase() === 'allow' ? 'green' : (e.result?.toLowerCase() === 'block' ? 'red' : '#d97706') }}>
                  {e.result ? e.result.toUpperCase() : 'NOT AVAILABLE'}
                </td>
                <td>{e.result?.toLowerCase() === 'block' ? 'Session Terminated' : 'Session Continued'}</td>
              </tr>
            ))}
          </tbody>
        </table>

        <h2>9. CHRONOLOGICAL EVENT RECONSTRUCTION</h2>
        <table className="evidence-table timeline-table">
          <thead>
            <tr>
              <th>Event ID</th>
              <th>Type</th>
              <th>Timestamp</th>
              <th>Source IP</th>
              <th>Action / Target</th>
              <th>Result</th>
            </tr>
          </thead>
          <tbody>
            {report.incident_timeline.map((e, i) => (
              <tr key={i}>
                <td>{e.event_id || `EVT-${i+1}`}</td>
                <td>{e.event_type || 'Unknown'}</td>
                <td>{formatDateIST(e.timestamp)}</td>
                <td>{e.ip_address || 'Not available'}</td>
                <td>{e.action}</td>
                <td>{e.result || 'N/A'}</td>
              </tr>
            ))}
          </tbody>
        </table>

        <h2>10. FINDINGS</h2>
        <div className="meta-info">
          <ul>
            <li><strong>Total Authenticated Activity:</strong> {report.investigation_findings.total_access_events} events evaluated.</li>
            <li><strong>Privilege Compliance:</strong> {report.investigation_findings.privilege_mismatches} mismatch(es) detected requiring Restrict enforcement.</li>
            <li><strong>Critical Violations:</strong> {report.investigation_findings.blocked_access_events} Block action(s) issued.</li>
          </ul>
        </div>

        <h2>11. INTEGRITY / EVIDENCE VERIFICATION</h2>
        <div className="meta-info" style={{ padding: '15px', border: '1px solid #ccc', backgroundColor: '#f9fafb' }}>
          <p><strong>Verification Status: </strong> 
            {integrityStatus ? (
              <span style={{ fontWeight: 'bold', color: integrityStatus.status === 'VALID' ? '#15803d' : '#b91c1c' }}>
                {integrityStatus.status}
              </span>
            ) : 'Pending...'}
          </p>
          {integrityStatus && integrityStatus.reason && (
             <p><strong>Detail:</strong> {integrityStatus.reason}</p>
          )}
          <p><strong>Mechanism:</strong> Real-time SHA-256 cryptographic hash-chain traversal.</p>
        </div>

        <h2>12. FORMAL CONCLUSION</h2>
        <div className="meta-info">
          <p>Based strictly on the cryptographically preserved evidence, this session demonstrates documented interaction with the organization's Zero Trust boundary. All risk assessments, SHAP explanations, and resulting enforcement actions (Allow, OTP, Restrict, Block) were executed deterministically in accordance with the established security posture.</p>
        </div>

        <h2>13. DISPOSITION</h2>
        <div className="meta-info">
          <p><strong>Evidence Source:</strong> Application-generated telemetry.</p>
          <p><strong>Storage:</strong> Zero Trust Evidence Log Database.</p>
          <p><strong>Action Required:</strong> Maintained for audit and compliance requirements.</p>
        </div>
      </div>
    </div>
  );
};

export default ForensicReport;
