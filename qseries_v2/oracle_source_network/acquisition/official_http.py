
from urllib.request import Request, urlopen
from datetime import datetime, timezone
import hashlib

DEFAULT_TIMEOUT_SECONDS = 8.0

def utc_now_iso():
    return datetime.now(timezone.utc).isoformat().replace("+00:00","Z")

def get_official_text(url: str, timeout: float = DEFAULT_TIMEOUT_SECONDS):
    timeout = float(timeout)
    if timeout <= 0 or timeout > 20:
        raise ValueError("timeout must be >0 and <=20 seconds")
    req = Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 QSeries-Oracle-OSN/1.0",
            "Accept": "text/html,application/xhtml+xml",
            "Connection": "close",
        },
        method="GET",
    )
    with urlopen(req, timeout=timeout) as r:
        status = getattr(r, "status", 200)
        body = r.read().decode("utf-8", errors="replace")
    if status != 200:
        raise RuntimeError(f"HTTP status {status}")
    if not body.strip():
        raise RuntimeError("empty official source body")
    return {
        "url": url,
        "observed_at": utc_now_iso(),
        "body": body,
        "payload_sha256": hashlib.sha256(body.encode("utf-8")).hexdigest(),
        "read_only": True,
        "execution_authority": False,
    }
