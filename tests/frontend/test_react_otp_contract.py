"""Contract for React Zero Trust OTP integration.

The Flask backend remains the authority for all Zero Trust policy decisions.
React only presents and submits the OTP step-up requirement returned by Flask.

Frozen behavior:

1. OTP HTTP 401 responses must be distinguishable from ordinary
   unauthenticated/session-expired 401 responses.
2. authService must expose POST /auth/otp/verify.
3. ResourceView must recognize requires_otp + policy_action=OTP.
4. Successful OTP verification must retry the same fetchFn.
5. The OTP form must accept an accessible six-digit numeric code.
"""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

AXIOS_PATH = (
    ROOT
    / "frontend"
    / "src"
    / "api"
    / "axios.js"
)

AUTH_SERVICE_PATH = (
    ROOT
    / "frontend"
    / "src"
    / "services"
    / "authService.js"
)

RESOURCE_VIEW_PATH = (
    ROOT
    / "frontend"
    / "src"
    / "components"
    / "resources"
    / "ResourceView.jsx"
)


def _read(path: Path) -> str:
    return path.read_text(
        encoding="utf-8"
    )


def test_axios_distinguishes_otp_401_from_session_expiry() -> None:
    source = _read(
        AXIOS_PATH
    )

    assert "requires_otp" in source
    assert "policy_action" in source
    assert '"OTP"' in source or "'OTP'" in source
    assert "401" in source


def test_auth_service_exposes_otp_verification_call() -> None:
    source = _read(
        AUTH_SERVICE_PATH
    )

    assert "verifyOtp" in source
    assert "/auth/otp/verify" in source
    assert "otp_code" in source


def test_resource_view_detects_otp_policy_response() -> None:
    source = _read(
        RESOURCE_VIEW_PATH
    )

    assert "requires_otp" in source
    assert "policy_action" in source
    assert "otpRequired" in source
    assert "otpCode" in source


def test_resource_view_submits_otp_and_retries_same_resource() -> None:
    source = _read(
        RESOURCE_VIEW_PATH
    )

    assert "authService.verifyOtp" in source
    assert "handleOtpSubmit" in source
    assert "fetchFn" in source
    assert "verified" in source


def test_resource_view_renders_accessible_six_digit_otp_ui() -> None:
    source = _read(
        RESOURCE_VIEW_PATH
    )

    assert 'inputMode="numeric"' in source
    assert "maxLength={6}" in source
    assert "Verify OTP" in source
    assert "otpCode" in source
