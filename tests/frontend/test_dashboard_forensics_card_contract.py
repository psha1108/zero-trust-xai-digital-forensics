"""Frontend contract for the dashboard Digital Forensics summary card.

The dashboard must reuse existing persisted Digital Forensics APIs.
React may provide admin-aware UX, but Flask remains the authorization
boundary. The card must never fabricate evidence or run ML/policy logic.
"""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


SERVICE = (
    ROOT
    / "security-frontend"
    / "src"
    / "services"
    / "forensicsService.js"
)


CARD = (
    ROOT
    / "security-frontend"
    / "src"
    / "components"
    / "dashboard"
    / "DigitalForensicsCard.jsx"
)


DASHBOARD = (
    ROOT
    / "security-frontend"
    / "src"
    / "pages"
    / "dashboard"
    / "Dashboard.jsx"
)


BACKEND = (
    ROOT
    / "app"
    / "routes"
    / "forensics.py"
)


def _read(path: Path) -> str:
    return path.read_text(
        encoding="utf-8"
    )


def test_existing_real_forensics_apis_are_reused() -> None:
    service = _read(
        SERVICE
    )

    backend = _read(
        BACKEND
    )

    required_service = (
        "getEvidence",
        "verifyIntegrity",
        "/forensics/evidence",
        "/forensics/verify",
    )

    for marker in required_service:
        assert marker in service

    assert (
        '@forensics_bp.route("/evidence", methods=["GET"])'
        in backend
    )

    assert (
        '@forensics_bp.route("/verify", methods=["GET"])'
        in backend
    )

    assert (
        "current_user.role"
        in backend
    )

    assert (
        '"admin"'
        in backend
    )


def test_digital_forensics_card_exists_and_is_admin_aware() -> None:
    assert CARD.exists()

    source = _read(
        CARD
    )

    required = (
        "useAuth",
        "user",
        "role",
        "admin",
        "Admin access required",
    )

    for marker in required:
        assert marker in source


def test_admin_card_uses_real_evidence_and_integrity_services() -> None:
    assert CARD.exists()

    source = _read(
        CARD
    )

    required = (
        "forensicsService.getEvidence",
        "forensicsService.verifyIntegrity",
        "evidence",
        "integrity",
        "created_at",
    )

    for marker in required:
        assert marker in source

    forbidden_fake_markers = (
        "Math.random",
        "fakeEvidence",
        "mockEvidence",
        "sampleEvidence",
        "dummyEvidence",
    )

    for marker in forbidden_fake_markers:
        assert marker not in source


def test_non_admin_path_does_not_request_privileged_forensics_data() -> None:
    assert CARD.exists()

    source = _read(
        CARD
    )

    required = (
        "user?.role",
        "admin",
        "return",
    )

    for marker in required:
        assert marker in source

    forbidden_security_logic = (
        "analyze_operational_access",
        "score_operational_record",
        "classify_operational_record",
        "cluster_operational_record",
        "explain_random_forest_prediction",
        "decide_zero_trust_policy",
        "apply_zero_trust_policy",
    )

    for marker in forbidden_security_logic:
        assert marker not in source


def test_dashboard_replaces_forensics_placeholder_with_real_card() -> None:
    source = _read(
        DASHBOARD
    )

    assert (
        "DigitalForensicsCard"
        in source
    )

    assert (
        "<DigitalForensicsCard"
        in source
    )

    assert (
        "No forensic investigation generated."
        not in source
    )
