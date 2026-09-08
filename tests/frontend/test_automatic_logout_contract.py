"""Contract for automatic logout on session termination.

The frontend must clear authentication state when the backend indicates
the session has been blocked or terminated due to high-risk or OTP failure.
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

AXIOS_PATH = (
    ROOT
    / "dummy"
    / "src"
    / "api"
    / "axios.js"
)

AUTH_CONTEXT_PATH = (
    ROOT
    / "dummy"
    / "src"
    / "context"
    / "AuthContext.jsx"
)

def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")

def test_axios_distinguishes_session_termination() -> None:
    source = _read(AXIOS_PATH)
    
    assert "policy_action" in source
    assert "Block" in source
    assert "OTP challenge locked." in source
    assert "session_expired" in source

def test_auth_context_listens_for_session_expired() -> None:
    source = _read(AUTH_CONTEXT_PATH)
    
    assert "session_expired" in source
    assert "setUser(null)" in source
