import hashlib
import json
from typing import Dict, Any
from app.extensions import db
from app.models import EvidenceLog

def preserve_evidence(login_event_id: int, details_dict: dict) -> EvidenceLog:
    """
    Creates a tamper-evident record for a security event.
    
    Must be called within an active transaction. The caller must execute
    db.session.commit() afterwards. 
    
    Concurrency is handled via with_for_update() where supported by the 
    underlying database (Note: this may not provide true row-level locking 
    on SQLite, but works as intended on PostgreSQL/MySQL).
    """
    # 1. Deterministic serialization (Text column representation)
    details_str = json.dumps(details_dict, sort_keys=True)
    
    # 2. Retrieve previous evidence hash
    # with_for_update() helps prevent concurrent events from reading the same 
    # previous_hash and forking the chain (where supported by the DB).
    last_log = EvidenceLog.query.order_by(EvidenceLog.id.desc()).with_for_update().first()
    
    previous_hash = last_log.record_hash if last_log else None
    
    # 3. Calculate new SHA-256 hash
    hash_input = details_str
    if previous_hash:
        hash_input += previous_hash
        
    current_hash = hashlib.sha256(hash_input.encode('utf-8')).hexdigest()
    
    # 4. Create EvidenceLog record (anchored to the session's login_event_id)
    new_evidence = EvidenceLog(
        login_event_id=login_event_id,
        details=details_str,
        record_hash=current_hash,
        previous_hash=previous_hash
    )
    
    # 5. Add to the session
    db.session.add(new_evidence)
    
    return new_evidence

def verify_evidence_chain() -> Dict[str, Any]:
    """
    Verifies the integrity of the entire EvidenceLog chain.
    Returns a dictionary with 'status' ("VALID" or "TAMPER DETECTED") 
    and 'reason' if tampering is detected.
    """
    # Fetch all records strictly in ascending ID order
    records = EvidenceLog.query.order_by(EvidenceLog.id.asc()).all()
    
    expected_previous_hash = None
    
    for record in records:
        # 1. Verify that the current record's previous_hash correctly points 
        # to the preceding record's hash.
        if record.previous_hash != expected_previous_hash:
            return {
                "status": "TAMPER DETECTED",
                "reason": f"Broken chain at ID {record.id}: previous_hash does not match preceding record_hash.",
                "affected_id": record.id
            }
            
        # 2. Recalculate the hash of the current record using the exact same logic
        hash_input = record.details
        if record.previous_hash:
            hash_input += record.previous_hash
            
        calculated_hash = hashlib.sha256(hash_input.encode('utf-8')).hexdigest()
        
        # 3. Verify that the stored record_hash hasn't been altered
        if calculated_hash != record.record_hash:
            return {
                "status": "TAMPER DETECTED",
                "reason": f"Data tampering at ID {record.id}: recalculated hash does not match stored record_hash.",
                "affected_id": record.id
            }
            
        # Update the expected hash for the next iteration in the loop
        expected_previous_hash = record.record_hash
        
    return {
        "status": "VALID",
        "reason": "All records passed integrity verification.",
        "affected_id": None
    }
