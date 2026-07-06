"""
ADP-011.1 — Production Auth Hardening

Hardens ADP-011 Live Kalshi Authentication.

Features:
- Read-only lock
- Auth state machine
- Safer diagnostics
- Environment validation
- Credential validation wrapper
- Optional Event Bus emission
- No trade execution
"""

import os
import time
import base64
from pathlib import Path
from dataclasses import dataclass
from enum import Enum
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


class KalshiAuthState(str, Enum):
    DISCONNECTED = "DISCONNECTED"
    CONFIGURED = "CONFIGURED"
    KEY_LOADED = "KEY_LOADED"
    CONNECTING = "CONNECTING"
    AUTHENTICATED = "AUTHENTICATED"
    ERROR = "ERROR"


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
    def normalized_environment(self) -> str:
        env = (self.environment or "demo").lower().strip()
        if env in ("prod", "production", "live"):
            return "production"
        if env in ("demo", "sandbox", "test"):
            return "demo"
        raise KalshiAuthError(
            f"Invalid KALSHI_ENV '{self.environment}'. Use demo or production."
        )

    @property
    def base_url(self) -> str:
        if self.normalized_environment == "production":
            return PRODUCTION_REST_BASE
        return DEMO_REST_BASE


class LiveKalshiAuthSession:
    def __init__(self, config: Optional[KalshiAuthConfig] = None, event_bus: Any = None):
        self.config = config or self.from_env()
        self.event_bus = event_bus
        self.private_key = None
        self.state = KalshiAuthState.DISCONNECTED
        self.last_error: Optional[str] = None
        self.last_validation: Optional[Dict[str, Any]] = None
        self.created_at = time.time()

        self._set_state(KalshiAuthState.CONFIGURED)
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

    def _emit(self, event_type: str, payload: Dict[str, Any]):
        if self.event_bus is None:
            return

        try:
            if hasattr(self.event_bus, "publish"):
                self.event_bus.publish(event_type, payload)
            elif hasattr(self.event_bus, "emit"):
                self.event_bus.emit(event_type, payload)
        except Exception:
            pass

    def _set_state(self, state: KalshiAuthState, error: Optional[str] = None):
        self.state = state
        self.last_error = error
        self._emit(
            "adp.kalshi.auth.state",
            {
                "adapter": "adp.kalshi",
                "module": "adp_011_1_auth_hardening",
                "state": state.value,
                "error": error,
                "timestamp": time.time(),
            },
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

    def _validate_config(self):
        if not self.config.api_key_id:
            raise KalshiAuthError("KALSHI_API_KEY_ID is missing.")

        if not self.config.private_key_path:
            raise KalshiAuthError("KALSHI_PRIVATE_KEY_PATH is missing.")

        _ = self.config.base_url

        if self.config.read_only is not True:
            raise KalshiAuthError("ADP-011.1 must run in read-only mode.")

    def _load_private_key(self):
        try:
            self._dependency_check()
            self._validate_config()

            key_path = Path(self.config.private_key_path).expanduser()
            if not key_path.exists():
                raise KalshiAuthError(f"Private key file not found: {key_path}")

            raw = key_path.read_bytes()

            password = os.getenv("KALSHI_PRIVATE_KEY_PASSWORD")
            password_bytes = password.encode("utf-8") if password else None

            self.private_key = serialization.load_pem_private_key(
                raw,
                password=password_bytes,
            )

            self._set_state(KalshiAuthState.KEY_LOADED)

        except Exception as exc:
            self._set_state(KalshiAuthState.ERROR, str(exc))
            raise

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
        if self.private_key is None:
            raise KalshiAuthError("Private key is not loaded.")

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
            raise KalshiAuthError("ADP-011.1 is read-only. Non-GET requests are blocked.")

        url = self.config.base_url.rstrip("/") + self._signed_path(path)

        headers = kwargs.pop("headers", {})
        merged_headers = self.auth_headers(method, path)
        merged_headers.update(headers)

        self._set_state(KalshiAuthState.CONNECTING)

        response = requests.request(
            method,
            url,
            headers=merged_headers,
            timeout=self.config.timeout_seconds,
            **kwargs,
        )

        return response

    def validate_credentials(self) -> Dict[str, Any]:
        result = {
            "module": "adp_011_1_auth_hardening",
            "status": "unknown",
            "state": self.state.value,
            "environment": self.config.normalized_environment,
            "base_url": self.config.base_url,
            "read_only": self.config.read_only,
            "authenticated": False,
            "http_status": None,
            "clock_timestamp_ms": self._timestamp_ms(),
            "error": None,
        }

        try:
            response = self.request("GET", "/portfolio/balance")
            result["http_status"] = response.status_code

            if 200 <= response.status_code < 300:
                result["status"] = "ok"
                result["authenticated"] = True
                self._set_state(KalshiAuthState.AUTHENTICATED)

                try:
                    result["response_keys"] = sorted(list(response.json().keys()))
                except Exception:
                    result["response_keys"] = []
            else:
                result["status"] = "error"
                result["error"] = response.text[:500]
                self._set_state(KalshiAuthState.ERROR, result["error"])

        except Exception as exc:
            result["status"] = "error"
            result["error"] = str(exc)
            self._set_state(KalshiAuthState.ERROR, str(exc))

        result["state"] = self.state.value
        self.last_validation = result

        self._emit(
            "adp.kalshi.auth.validation",
            {
                "adapter": "adp.kalshi",
                "authenticated": result["authenticated"],
                "status": result["status"],
                "state": result["state"],
                "http_status": result["http_status"],
                "environment": result["environment"],
                "timestamp": time.time(),
            },
        )

        return result

    def diagnostics(self) -> Dict[str, Any]:
        key_path = self.config.private_key_path or ""

        return {
            "module": "adp_011_1_auth_hardening",
            "status": "ok" if self.state != KalshiAuthState.ERROR else "error",
            "state": self.state.value,
            "environment": self.config.normalized_environment,
            "base_url": self.config.base_url,
            "read_only": self.config.read_only,
            "has_api_key_id": bool(self.config.api_key_id),
            "api_key_preview": self.config.api_key_id[:6] + "..." if self.config.api_key_id else None,
            "has_private_key_path": bool(key_path),
            "private_key_file_name": Path(key_path).name if key_path else None,
            "private_key_loaded": self.private_key is not None,
            "last_error": self.last_error,
            "last_validation": self.last_validation,
        }


def build_live_kalshi_auth_session(event_bus: Any = None) -> LiveKalshiAuthSession:
    return LiveKalshiAuthSession(event_bus=event_bus)


if __name__ == "__main__":
    session = build_live_kalshi_auth_session()
    print(session.diagnostics())
    print(session.validate_credentials())
