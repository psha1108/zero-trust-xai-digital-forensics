from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

SERVICE_PATH = (
    ROOT
    / "security-frontend"
    / "src"
    / "services"
    / "dashboardService.js"
)

SESSION_CARD_PATH = (
    ROOT
    / "security-frontend"
    / "src"
    / "components"
    / "dashboard"
    / "SessionStatusCard.jsx"
)

BACKEND_PATH = (
    ROOT
    / "app"
    / "routes"
    / "dashboard.py"
)


def _read(path: Path) -> str:
    return path.read_text(
        encoding="utf-8"
    )


def test_backend_dashboard_routes_already_exist() -> None:
    source = _read(
        BACKEND_PATH
    )

    assert (
        '@dashboard_bp.route("/session-status"'
        in source
    )

    assert (
        '@dashboard_bp.route("/login-history"'
        in source
    )

    assert (
        '@dashboard_bp.route("/access-history"'
        in source
    )


def test_dashboard_service_calls_real_session_status_api() -> None:
    source = _read(
        SERVICE_PATH
    )

    assert (
        "getSessionStatus:"
        in source
    )

    assert (
        "axiosInstance.get('/dashboard/session-status')"
        in source
    )


def test_dashboard_service_calls_real_login_history_api() -> None:
    source = _read(
        SERVICE_PATH
    )

    assert (
        "axiosInstance.get('/dashboard/login-history')"
        in source
    )


def test_dashboard_service_calls_real_access_history_api() -> None:
    source = _read(
        SERVICE_PATH
    )

    assert (
        "axiosInstance.get('/dashboard/access-history')"
        in source
    )


def test_session_status_card_uses_backend_session_data() -> None:
    source = _read(
        SESSION_CARD_PATH
    )

    assert (
        "dashboardService"
        in source
    )

    assert (
        "getSessionStatus"
        in source
    )

    assert (
        "started_at"
        in source
    )

    assert (
        "current_ip"
        in source
    )

    assert (
        "is_active"
        in source
    )
