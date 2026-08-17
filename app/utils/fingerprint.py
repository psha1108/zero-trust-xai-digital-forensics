import hashlib
import secrets


def get_device_fingerprint(user_agent: str) -> str:
    """
    Reduces a full User-Agent string down to a short, stable fingerprint
    based on browser family + OS family only — ignoring version numbers.
    Prevents a routine browser update from looking like a "new device."
    """
    ua = (user_agent or "unknown").lower()

    if "edg" in ua:
        browser = "edge"
    elif "chrome" in ua:
        browser = "chrome"
    elif "firefox" in ua:
        browser = "firefox"
    elif "safari" in ua:
        browser = "safari"
    else:
        browser = "other"

    if "windows" in ua:
        os_family = "windows"
    elif "mac os" in ua or "macintosh" in ua:
        os_family = "macos"
    elif "linux" in ua:
        os_family = "linux"
    elif "android" in ua:
        os_family = "android"
    elif "iphone" in ua or "ipad" in ua:
        os_family = "ios"
    else:
        os_family = "other"

    return f"{browser}-{os_family}"


def generate_session_id() -> str:
    """
    Generates a fresh, random, unique session identifier at login time.
    Stored inside flask.session (so it survives across requests via the
    signed cookie) rather than derived by hashing the cookie itself —
    this avoids the chicken-and-egg problem of needing the cookie's
    final value before Flask has actually sent it to the browser.
    """
    return secrets.token_hex(32)  # 64 hex characters, matches our DB column size