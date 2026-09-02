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
            details_json = r.details
            
        results.append({
            "id": r.id,
            "login_event_id": r.login_event_id,
            "created_at": r.created_at.isoformat() if r.created_at else None,
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
        events.append({
            "timestamp": acc.timestamp.isoformat() if acc.timestamp else None,
            "event_type": "AccessEvent",
            "user_id": acc.user_id,
            "session_id": acc.session_id,
            "ip_address": acc.ip_address,
            "device_info": acc.device_id,
            "action": f"access {acc.resource}",
            "result": acc.decision if acc.decision else "unknown",
            "risk_score": getattr(acc, "risk_score", None),
            "privilege_mismatch": acc.privilege_mismatch
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
        inventory.append({
            "evidence_id": log.id,
            "timestamp": log.created_at.isoformat() if log.created_at else None,
            "record_hash": log.record_hash,
            "previous_hash": log.previous_hash
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
