from pathlib import Path

ROOT = Path("qseries_v2")
ADAPTERS = ROOT / "adapters"
ADAPTERS.mkdir(parents=True, exist_ok=True)

auth_code = r'''"""
ADP-011 — Live Kalshi Authentication

Read-only Kalshi authentication/session manager.
Oracle may consume authenticated market/account diagnostics.
Oracle never executes trades.
"""

import os
import time
import base64
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, Optional, Any
from urllib.parse import urlparse

try:
    import requests
except Exception:
    requests = None

try:
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import padding
except Exception:
    hashes = None
    serialization = None
    padding = None


PRODUCTION_REST_BASE = "https://external-api.kalshi.com/trade-api/v2"
DEMO_REST_BASE = "https://external-api.demo.kalshi.co/trade-api/v2"


class KalshiAuthError(Exception):
    pass


@dataclass
class KalshiAuthConfig:
    api_key_id: str
    private_key_path: str
    environment: str = "demo"
    read_only: bool = True
    timeout_seconds: float = 10.0

    @property
    def base_url(self) -> str:
        env = (self.environment or "demo").lower().strip()
        if env in ("prod", "production", "live"):
            return PRODUCTION_REST_BASE
        return DEMO_REST_BASE


class LiveKalshiAuthSession:
    def __init__(self, config: Optional[KalshiAuthConfig] = None):
        self.config = config or self.from_env()
        self.private_key = None
        self.last_validation: Optional[Dict[str, Any]] = None
        self._load_private_key()

    @staticmethod
    def from_env() -> KalshiAuthConfig:
        return KalshiAuthConfig(
            api_key_id=os.getenv("KALSHI_API_KEY_ID", "").strip(),
            private_key_path=os.getenv("KALSHI_PRIVATE_KEY_PATH", "").strip(),
            environment=os.getenv("KALSHI_ENV", "demo").strip() or "demo",
            read_only=True,
            timeout_seconds=float(os.getenv("KALSHI_TIMEOUT_SECONDS", "10")),
        )

    def _dependency_check(self):
        missing = []
        if requests is None:
            missing.append("requests")
        if serialization is None or hashes is None or padding is None:
            missing.append("cryptography")
        if missing:
            raise KalshiAuthError(
                "Missing dependency/dependencies: "
                + ", ".join(missing)
                + ". Install with: pip install requests cryptography"
            )

    def _load_private_key(self):
        self._dependency_check()

        if not self.config.api_key_id:
            raise KalshiAuthError("KALSHI_API_KEY_ID is missing.")

        if not self.config.private_key_path:
            raise KalshiAuthError("KALSHI_PRIVATE_KEY_PATH is missing.")

        key_path = Path(self.config.private_key_path).expanduser()
        if not key_path.exists():
            raise KalshiAuthError(f"Private key file not found: {key_path}")

        raw = key_path.read_bytes()
        try:
            self.private_key = serialization.load_pem_private_key(raw, password=None)
        except Exception as exc:
            raise KalshiAuthError(f"Unable to load private key: {exc}") from exc

    def _timestamp_ms(self) -> str:
        return str(int(time.time() * 1000))

    def _signed_path(self, path_or_url: str) -> str:
        if path_or_url.startswith("http://") or path_or_url.startswith("https://"):
            parsed = urlparse(path_or_url)
            return parsed.path
        if not path_or_url.startswith("/"):
            path_or_url = "/" + path_or_url
        return path_or_url

    def sign(self, method: str, path_or_url: str, timestamp_ms: Optional[str] = None) -> str:
        timestamp_ms = timestamp_ms or self._timestamp_ms()
        method = method.upper().strip()
        path = self._signed_path(path_or_url)

        message = f"{timestamp_ms}{method}{path}".encode("utf-8")
        signature = self.private_key.sign(
            message,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.DIGEST_LENGTH,
            ),
            hashes.SHA256(),
        )
        return base64.b64encode(signature).decode("utf-8")

    def auth_headers(self, method: str, path_or_url: str) -> Dict[str, str]:
        timestamp = self._timestamp_ms()
        return {
            "KALSHI-ACCESS-KEY": self.config.api_key_id,
            "KALSHI-ACCESS-TIMESTAMP": timestamp,
            "KALSHI-ACCESS-SIGNATURE": self.sign(method, path_or_url, timestamp),
            "Content-Type": "application/json",
        }

    def request(self, method: str, path: str, **kwargs):
        method = method.upper().strip()

        if self.config.read_only and method not in ("GET", "HEAD", "OPTIONS"):
            raise KalshiAuthError("ADP-011 is read-only. Non-GET requests are blocked.")

        url = self.config.base_url.rstrip("/") + self._signed_path(path)
        headers = kwargs.pop("headers", {})
        merged_headers = self.auth_headers(method, path)
        merged_headers.update(headers)

        return requests.request(
            method,
            url,
            headers=merged_headers,
            timeout=self.config.timeout_seconds,
            **kwargs,
        )

    def validate_credentials(self) -> Dict[str, Any]:
        """
        Uses authenticated portfolio balance endpoint.
        This confirms key id, private key signing, environment, and session readiness.
        """
        result = {
            "module": "adp_011_live_kalshi_authentication",
            "status": "unknown",
            "environment": self.config.environment,
            "base_url": self.config.base_url,
            "read_only": self.config.read_only,
            "authenticated": False,
            "http_status": None,
            "error": None,
        }

        try:
            response = self.request("GET", "/portfolio/balance")
            result["http_status"] = response.status_code

            if 200 <= response.status_code < 300:
                result["status"] = "ok"
                result["authenticated"] = True
                try:
                    result["response_keys"] = sorted(list(response.json().keys()))
                except Exception:
                    result["response_keys"] = []
            else:
                result["status"] = "error"
                result["error"] = response.text[:500]

        except Exception as exc:
            result["status"] = "error"
            result["error"] = str(exc)

        self.last_validation = result
        return result

    def diagnostics(self) -> Dict[str, Any]:
        return {
            "module": "adp_011_live_kalshi_authentication",
            "status": "ok",
            "environment": self.config.environment,
            "base_url": self.config.base_url,
            "read_only": self.config.read_only,
            "has_api_key_id": bool(self.config.api_key_id),
            "has_private_key_path": bool(self.config.private_key_path),
            "private_key_loaded": self.private_key is not None,
            "last_validation": self.last_validation,
        }


def build_live_kalshi_auth_session() -> LiveKalshiAuthSession:
    return LiveKalshiAuthSession()


if __name__ == "__main__":
    session = build_live_kalshi_auth_session()
    print(session.diagnostics())
    print(session.validate_credentials())
'''

test_code = r'''"""
Test ADP-011 without hitting live Kalshi.

This validates:
- config object
- RSA private key loading
- Kalshi-style signature creation
- read-only write blocking
- diagnostics
"""

import tempfile
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization

from qseries_v2.adapters.live_kalshi_authentication import (
    KalshiAuthConfig,
    LiveKalshiAuthSession,
    KalshiAuthError,
)


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


def test_adp_011():
    key_path = make_test_key_file()

    config = KalshiAuthConfig(
        api_key_id="test-key-id",
        private_key_path=key_path,
        environment="demo",
        read_only=True,
    )

    session = LiveKalshiAuthSession(config)
    sig = session.sign("GET", "/portfolio/balance", "1703123456789")
    headers = session.auth_headers("GET", "/portfolio/balance")
    diag = session.diagnostics()

    assert sig and isinstance(sig, str)
    assert headers["KALSHI-ACCESS-KEY"] == "test-key-id"
    assert "KALSHI-ACCESS-SIGNATURE" in headers
    assert diag["status"] == "ok"
    assert diag["read_only"] is True
    assert diag["private_key_loaded"] is True

    try:
        session.request("POST", "/portfolio/orders", json={})
        raise AssertionError("POST should have been blocked in read-only mode")
    except KalshiAuthError:
        pass

    Path(key_path).unlink(missing_ok=True)

    print("[PASS] ADP-011 Live Kalshi Authentication")
    print(diag)


if __name__ == "__main__":
    test_adp_011()
'''

init_code = '''try:
    from .live_kalshi_authentication import (
        KalshiAuthConfig,
        LiveKalshiAuthSession,
        build_live_kalshi_auth_session,
    )
except Exception:
    pass
'''

(ADAPTERS / "live_kalshi_authentication.py").write_text(auth_code, encoding="utf-8")
(ADAPTERS / "__init__.py").write_text(init_code, encoding="utf-8")
Path("test_adp_011_live_kalshi_authentication.py").write_text(test_code, encoding="utf-8")

print("========================================")
print(" ADP-011 INSTALLER")
print(" Live Kalshi Authentication")
print("========================================")
print("[OK] Wrote qseries_v2\\adapters\\live_kalshi_authentication.py")
print("[OK] Wrote qseries_v2\\adapters\\__init__.py")
print("[OK] Wrote test_adp_011_live_kalshi_authentication.py")
print()
print("[DONE] ADP-011 installed")
print()
print("Run:")
print("python test_adp_011_live_kalshi_authentication.py")
print()
print("For real credential validation later:")
print("set KALSHI_API_KEY_ID=your-key-id")
print("set KALSHI_PRIVATE_KEY_PATH=C:\\path\\to\\your\\kalshi.key")
print("set KALSHI_ENV=demo")
print("python -m qseries_v2.adapters.live_kalshi_authentication")