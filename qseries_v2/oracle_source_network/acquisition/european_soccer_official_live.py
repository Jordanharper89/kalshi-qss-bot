
from .official_http import get_official_text
from datetime import datetime, timezone
import hashlib
import subprocess

EPL_FIXTURES_URL = "https://www.premierleague.com/en/news/4675097/all-380-fixtures-for-202627-premier-league-season"

UCL_OFFICIAL_URLS = (
    "https://www.uefa.com/uefachampionsleague/fixtures-results/",
    "https://www.uefa.com/uefachampionsleague/news/02a8-2174c9e9019d-f909a77bd77a-1000--2026-27-champions-league-all-the-league-phase-fixtures/",
)

def acquire_epl_fixtures(timeout=8.0):
    s = get_official_text(EPL_FIXTURES_URL, timeout=timeout)
    low = s["body"].lower()
    s.update({
        "provider": "premier_league_official",
        "league": "EPL",
        "source_authority": "official_league",
        "markers": {
            "premier_league": "premier league" in low,
            "fixtures": "fixture" in low,
            "2026_27": ("2026/27" in low or "2026-27" in low or "202627" in low),
        },
    })
    return s

def _ucl_markers(body):
    low = body.lower()
    return {
        "champions_league": ("champions league" in low or "uefa champions league" in low),
        "competition_identity": ("uefachampionsleague" in low or "champions league" in low),
        "fixtures_or_matches": ("fixture" in low or "matches" in low or "matchday" in low),
    }

def _curl_official_text(url, timeout=7.0):
    timeout = max(1, min(int(float(timeout)), 8))
    cmd = [
        "curl.exe",
        "--location",
        "--fail",
        "--silent",
        "--show-error",
        "--compressed",
        "--connect-timeout", "4",
        "--max-time", str(timeout),
        "--user-agent", "Mozilla/5.0 QSeries-Oracle-OSN/1.0",
        "--header", "Accept: text/html,application/xhtml+xml",
        url,
    ]

    try:
        p = subprocess.run(
            cmd,
            text=False,
            capture_output=True,
            timeout=timeout + 3,
        )
    except FileNotFoundError as exc:
        raise RuntimeError("curl.exe is not available on this Windows runtime") from exc
    except subprocess.TimeoutExpired as exc:
        raise TimeoutError(f"curl.exe outer timeout exceeded for {url}") from exc

    if p.returncode != 0:
        err = p.stderr.decode("utf-8", errors="replace").strip()
        raise RuntimeError(f"curl.exe failed rc={p.returncode}: {err}")

    raw = p.stdout
    if not raw:
        raise RuntimeError("curl.exe returned an empty UEFA payload")

    body = raw.decode("utf-8", errors="replace")
    return {
        "url": url,
        "observed_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "body": body,
        "payload_sha256": hashlib.sha256(raw).hexdigest(),
        "read_only": True,
        "execution_authority": False,
        "transport": "curl.exe",
    }

def acquire_ucl_fixtures(timeout=7.0):
    errors = []

    for url in UCL_OFFICIAL_URLS:
        # First retain the already-certified stdlib path as the preferred transport.
        try:
            s = get_official_text(url, timeout=min(float(timeout), 4.0))
            markers = _ucl_markers(s["body"])
            if all(markers.values()):
                s.update({
                    "provider": "uefa_official",
                    "league": "UCL",
                    "source_authority": "official_governing_body",
                    "markers": markers,
                    "selected_official_url": url,
                    "transport": "urllib",
                })
                return s
            errors.append(f"urllib {url}: marker validation failed {markers}")
        except Exception as exc:
            errors.append(f"urllib {url}: {type(exc).__name__}: {exc}")

        # Windows curl uses a different transport/TLS stack and is independently bounded.
        try:
            s = _curl_official_text(url, timeout=timeout)
            markers = _ucl_markers(s["body"])
            if all(markers.values()):
                s.update({
                    "provider": "uefa_official",
                    "league": "UCL",
                    "source_authority": "official_governing_body",
                    "markers": markers,
                    "selected_official_url": url,
                })
                return s
            errors.append(f"curl {url}: marker validation failed {markers}")
        except Exception as exc:
            errors.append(f"curl {url}: {type(exc).__name__}: {exc}")

    raise RuntimeError(
        "all bounded official UEFA transports failed | " + " | ".join(errors)
    )
