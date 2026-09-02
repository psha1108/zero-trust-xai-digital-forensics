from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

APP = ROOT / "frontend" / "src" / "App.jsx"

PROTECTED_ROUTE = (
    ROOT
    / "frontend"
    / "src"
    / "components"
    / "ProtectedRoute.jsx"
)

ADMIN_ROUTE = (
    ROOT
    / "frontend"
    / "src"
    / "components"
    / "AdminRoute.jsx"
)

SIDEBAR = (
    ROOT
    / "frontend"
    / "src"
    / "components"
    / "layout"
    / "Sidebar.jsx"
)


def read(path):
    return path.read_text(
        encoding="utf-8"
    )


def test_digital_forensics_has_dedicated_admin_route_guard():
    assert ADMIN_ROUTE.exists(), (
        "Digital Forensics needs a dedicated AdminRoute. "
        "ProtectedRoute must remain authentication-only."
    )

    source = read(ADMIN_ROUTE)

    required = (
        "useAuth",
        "Navigate",
        "Outlet",
        "user",
        "role",
        "'admin'",
        '"/dashboard"',
    )

    for marker in required:
        assert marker in source, (
            f"AdminRoute missing marker: {marker}"
        )


def test_forensics_routes_are_nested_under_admin_route():
    source = read(APP)

    assert "import AdminRoute" in source

    assert (
        "<Route element={<AdminRoute />}>"
        in source
    )

    for path in (
        'path="/forensics"',
        'path="/forensics/evidence"',
        'path="/forensics/timeline/:sessionId"',
        'path="/forensics/report/:sessionId"',
    ):
        assert path in source

    admin_guard_position = source.index(
        "<Route element={<AdminRoute />}>"
    )

    first_forensics_position = source.index(
        'path="/forensics"'
    )

    assert (
        admin_guard_position
        < first_forensics_position
    )


def test_general_protected_route_remains_authentication_only():
    source = read(PROTECTED_ROUTE)

    assert "useAuth" in source
    assert "Navigate" in source
    assert "Outlet" in source
    assert 'to="/login"' in source

    assert "role" not in source.lower()
    assert "admin" not in source.lower()


def test_resource_navigation_remains_available_for_zero_trust_demo():
    app_source = read(APP)
    sidebar_source = read(SIDEBAR)

    resource_paths = (
        "/resources/normal",
        "/resources/hr",
        "/resources/finance",
        "/resources/admin",
    )

    for path in resource_paths:
        assert path in app_source
        assert path in sidebar_source

    assert "Admin Controls" in sidebar_source

    # The admin resource must NOT be hidden behind the
    # Digital Forensics AdminRoute. Non-admin access is
    # intentionally evaluated by Flask Zero Trust policy
    # to create privilege_mismatch evidence.
    assert (
        '<Route path="/resources/admin"'
        in app_source
    )


def test_forensics_sidebar_remains_admin_only():
    source = read(SIDEBAR)

    assert "user.role === 'admin'" in source
    assert 'to="/forensics"' in source
    assert "Digital Forensics" in source
    assert "Admin only" in source
    assert "disabled" in source