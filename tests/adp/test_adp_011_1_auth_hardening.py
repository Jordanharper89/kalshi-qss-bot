"""
Test ADP-011.1 without hitting live Kalshi.

Validates:
- RSA key loading
- signing
- headers
- read-only blocking
- environment validation
- state machine
- optional event bus emission
"""

import tempfile
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization

from qseries_v2.adapters.live_kalshi_authentication import (
    KalshiAuthConfig,
    LiveKalshiAuthSession,
    KalshiAuthError,
    KalshiAuthState,
)


class FakeEventBus:
    def __init__(self):
        self.events = []

    def publish(self, event_type, payload):
        self.events.append((event_type, payload))


def make_test_key_file():
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    raw = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )

    temp = tempfile.NamedTemporaryFile(delete=False, suffix=".key")
    temp.write(raw)
    temp.close()
    return temp.name


def test_adp_011_1():
    key_path = make_test_key_file()
    event_bus = FakeEventBus()

    config = KalshiAuthConfig(
        api_key_id="test-key-id",
        private_key_path=key_path,
        environment="demo",
        read_only=True,
    )

    session = LiveKalshiAuthSession(config=config, event_bus=event_bus)

    sig = session.sign("GET", "/portfolio/balance", "1703123456789")
    headers = session.auth_headers("GET", "/portfolio/balance")
    diag = session.diagnostics()

    assert sig and isinstance(sig, str)
    assert headers["KALSHI-ACCESS-KEY"] == "test-key-id"
    assert "KALSHI-ACCESS-SIGNATURE" in headers
    assert diag["status"] == "ok"
    assert diag["read_only"] is True
    assert diag["private_key_loaded"] is True
    assert session.state == KalshiAuthState.KEY_LOADED
    assert len(event_bus.events) >= 1

    try:
        session.request("POST", "/portfolio/orders", json={})
        raise AssertionError("POST should have been blocked in read-only mode")
    except KalshiAuthError:
        pass

    bad_env_config = KalshiAuthConfig(
        api_key_id="test-key-id",
        private_key_path=key_path,
        environment="bad-env",
        read_only=True,
    )

    try:
        LiveKalshiAuthSession(config=bad_env_config)
        raise AssertionError("Bad environment should fail")
    except KalshiAuthError:
        pass

    not_read_only_config = KalshiAuthConfig(
        api_key_id="test-key-id",
        private_key_path=key_path,
        environment="demo",
        read_only=False,
    )

    try:
        LiveKalshiAuthSession(config=not_read_only_config)
        raise AssertionError("Non-read-only mode should fail")
    except KalshiAuthError:
        pass

    Path(key_path).unlink(missing_ok=True)

    print("[PASS] ADP-011.1 Production Auth Hardening")
    print(diag)


if __name__ == "__main__":
    test_adp_011_1()
