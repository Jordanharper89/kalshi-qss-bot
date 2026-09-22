
from urllib.request import Request, urlopen
import json

DEFAULT_TIMEOUT_SECONDS = 8.0

def get_json(url: str, timeout: float = DEFAULT_TIMEOUT_SECONDS):
    timeout = float(timeout)
    if timeout <= 0 or timeout > 20:
        raise ValueError("OSN HTTP timeout must be >0 and <=20 seconds")
    req = Request(
        url,
        headers={
            "User-Agent": "QSeries-Oracle-OSN/1.0",
            "Accept": "application/json",
            "Connection": "close",
        },
        method="GET",
    )
    with urlopen(req, timeout=timeout) as r:
        status = getattr(r, "status", 200)
        if status != 200:
            raise RuntimeError(f"HTTP status {status}")
        return json.loads(r.read().decode("utf-8"))
