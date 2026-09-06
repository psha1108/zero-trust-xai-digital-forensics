import json
from flask import Blueprint, jsonify
from flask_login import login_required, current_user

from app.models import EvidenceLog, Session, LoginEvent, AccessEvent
from app.utils.forensics_utils import verify_evidence_chain

forensics_bp = Blueprint("forensics", __name__, url_prefix="/api/forensics")

def _require_admin():
    if not current_user.is_authenticated or current_user.role != "admin":
        return jsonify({"error": "Forbidden - admin role required."}), 403
    return None

@forensics_bp.route("/evidence", methods=["GET"])
@login_required
def get_evidence():
    auth_err = _require_admin()
    if auth_err: return auth_err
    
    records = EvidenceLog.query.order_by(EvidenceLog.id.asc()).all()
    results = []
    for r in records:
        try:
            details_json = json.loads(r.details)
        except:
            details_json = {"raw": r.details}
            
        event_id = None
        event_type = "Unknown"
        session_id = None
        timestamp = None
        user = "unknown"
        resource = None
        risk = None
        policy_decision = None
        
        # New structure
        if "event" in details_json:
            event_info = details_json.get("event", {})
            event_id = event_info.get("event_id")
            event_type = event_info.get("event_type", "Unknown")
            session_id = details_json.get("session_id")
            timestamp = details_json.get("timestamp")
            
            user_info = details_json.get("user", {})
            user = user_info.get("username", "unknown")
            
            resource_info = details_json.get("resource", {})
            resource = resource_info.get("name")
            
            ml_info = details_json.get("ml", {}).get("random_forest", {})
            risk = ml_info.get("risk_label")
            
            zt_info = details_json.get("zero_trust", {})
            policy_decision = zt_info.get("policy_decision")
        else:
            # Old structure backward compatibility
            event_type = details_json.get("event_type", "Unknown")
            if event_type == "LoginEvent":
                event_id = details_json.get("login_event_id", r.login_event_id)
            elif event_type == "AccessEvent":
                event_id = details_json.get("access_event_id")
            
            session_id = details_json.get("session_id")
            timestamp = details_json.get("timestamp")
            user = details_json.get("username_attempted") or "unknown"
            resource = details_json.get("resource")
            
        if user == "unknown" and session_id:
            # Try to resolve user from Session
            s = Session.query.filter_by(session_id=session_id).first()
            if s:
                from app.models import User
                u = User.query.get(s.user_id)
                if u:
                    user = u.username
                    
        if user == "unknown":
            user = "Not available"
            
        results.append({
            "evidence_id": r.id,
            "event_id": event_id,
            "event_type": event_type,
            "login_event_id": r.login_event_id,
            "session_id": session_id,
            "timestamp": timestamp or (r.created_at.isoformat() if r.created_at else None),
            "user": user,
            "resource": resource,
            "risk": risk,
            "policy_decision": policy_decision,
            "record_hash": r.record_hash,
            "previous_hash": r.previous_hash,
            "details": details_json
        })
    return jsonify(results), 200

@forensics_bp.route("/verify", methods=["GET"])
@login_required
def verify_integrity():
    auth_err = _require_admin()
    if auth_err: return auth_err
    
    result = verify_evidence_chain()
    return jsonify(result), 200

def _get_timeline_events(session_id):
    session_row = Session.query.filter_by(session_id=session_id).first()
    if not session_row:
        return None
        
    events = []
    
    # 1. Login Event
    login = LoginEvent.query.get(session_row.login_event_id)
    if login:
        events.append({
            "event_id": login.id,
            "timestamp": login.timestamp.isoformat() if login.timestamp else None,
            "event_type": "LoginEvent",
            "user_id": login.user_id,
            "session_id": session_id,
            "ip_address": login.ip_address,
            "device_info": login.device_info,
            "action": "login",
            "result": "success" if login.success else "failed",
            "risk_label": getattr(login, "risk_label", None),
            "anomaly_score": getattr(login, "anomaly_score", None),
            "cluster_id": getattr(login, "cluster_id", None)
        })
        
    # 2. Access Events
    accesses = AccessEvent.query.filter_by(session_id=session_id).all()
    for acc in accesses:
        # Fetch the corresponding evidence log to extract ML fields that aren't natively in the AccessEvent table
        risk_label = None
        anomaly_score = None
        cluster_id = None
        policy_reason = None
        policy_decision = None
        
        # We need to find the EvidenceLog where details->event->event_id == acc.id and event_type == AccessEvent
        log = EvidenceLog.query.filter_by(login_event_id=session_row.login_event_id).all()
        for l in log:
            try:
                details = json.loads(l.details)
                if details.get("event", {}).get("event_type") == "AccessEvent" and details.get("event", {}).get("event_id") == acc.id:
                    ml = details.get("ml", {})
                    risk_label = ml.get("random_forest", {}).get("risk_label")
                    risk_score = ml.get("random_forest", {}).get("risk_score")
                    anomaly_score = ml.get("isolation_forest", {}).get("anomaly_score")
                    cluster_id = ml.get("kmeans", {}).get("cluster_id")
                    zt = details.get("zero_trust", {})
                    policy_reason = zt.get("reason")
                    policy_decision = zt.get("policy_decision")
                    break
                elif details.get("event_type") == "AccessEvent" and details.get("access_event_id") == acc.id:
                    ml = details.get("ml", {})
                    risk_label = ml.get("random_forest", {}).get("risk_label")
                    risk_score = ml.get("random_forest", {}).get("risk_score")
                    anomaly_score = ml.get("isolation_forest", {}).get("anomaly_score")
                    cluster_id = ml.get("kmeans", {}).get("cluster_id")
                    zt = details.get("zero_trust", {})
                    policy_reason = zt.get("reason")
                    policy_decision = zt.get("policy_decision")
                    break
            except:
                pass

        events.append({
            "event_id": acc.id,
            "timestamp": acc.timestamp.isoformat() if acc.timestamp else None,
            "event_type": "AccessEvent",
            "user_id": acc.user_id,
            "session_id": acc.session_id,
            "resource": acc.resource,
            "ip_address": acc.ip_address,
            "device_info": acc.device_id,
            "action": f"access {acc.resource}",
            "result": acc.decision if acc.decision else "unknown",
            "decision": acc.decision if acc.decision else "unknown",
            "risk_score": getattr(acc, "risk_score", risk_score if 'risk_score' in locals() else None),
            "risk_label": risk_label,
            "anomaly_score": anomaly_score,
            "cluster_id": cluster_id,
            "privilege_mismatch": acc.privilege_mismatch,
            "policy_reason": policy_reason,
            "policy_decision": policy_decision
        })
        
    # Sort chronologically
    events.sort(key=lambda x: x["timestamp"] if x["timestamp"] else "")
    return events, session_row

@forensics_bp.route("/timeline/<session_id>", methods=["GET"])
@login_required
def get_timeline(session_id):
    auth_err = _require_admin()
    if auth_err: return auth_err
    
    result = _get_timeline_events(session_id)
    if not result:
        return jsonify({"error": "Session not found"}), 404
        
    events, _ = result
    return jsonify(events), 200

@forensics_bp.route("/report/<session_id>", methods=["GET"])
@login_required
def get_report(session_id):
    auth_err = _require_admin()
    if auth_err: return auth_err
    
    result = _get_timeline_events(session_id)
    if not result:
        return jsonify({"error": "Session not found"}), 404
        
    events, session_row = result
    
    # Evidence inventory
    evidence_logs = EvidenceLog.query.filter_by(login_event_id=session_row.login_event_id).order_by(EvidenceLog.id.asc()).all()
    inventory = []
    for log in evidence_logs:
        try:
            details_json = json.loads(log.details)
        except:
            details_json = {"raw": log.details}
            
        inventory.append({
            "evidence_id": log.id,
            "timestamp": log.created_at.isoformat() if log.created_at else None,
            "record_hash": log.record_hash,
            "previous_hash": log.previous_hash,
            "details": details_json
        })
        
    # Findings
    total_accesses = len([e for e in events if e["event_type"] == "AccessEvent"])
    
    # "decision" represents actual AccessEvent.decision (Blocked/Denied/Allow)
    blocked_accesses = len([
        e for e in events 
        if e["event_type"] == "AccessEvent" 
        and e.get("result") and e.get("result").lower() in ("block", "blocked", "deny", "denied")
    ])
    
    privilege_mismatches = len([
        e for e in events 
        if e["event_type"] == "AccessEvent" and e.get("privilege_mismatch")
    ])
    
    report = {
        "report_identification": {
            "report_id": f"REP-{session_row.id}",
            "timestamp": session_row.started_at.isoformat() if session_row.started_at else None,
            "user_id": session_row.user_id,
            "session_id": session_row.session_id
        },
        "incident_overview": {
            "start_time": session_row.started_at.isoformat() if session_row.started_at else None,
            "end_time": session_row.ended_at.isoformat() if session_row.ended_at else None,
            "session_status": "inactive" if not session_row.is_active else "active"
        },
        "evidence_inventory": inventory,
        "incident_timeline": events,
        "investigation_findings": {
            "total_access_events": total_accesses,
            "blocked_access_events": blocked_accesses,
            "privilege_mismatches": privilege_mismatches
        }
    }
    
    return jsonify(report), 200
