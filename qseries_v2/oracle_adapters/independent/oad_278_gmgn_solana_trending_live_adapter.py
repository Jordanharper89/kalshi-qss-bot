from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
import subprocess

from .oad_277_gmgn_production_admission_boundary import require_gmgn_admission

READ_ONLY = True
PROBABILITY_ENABLED = False
DIRECTION_ENABLED = False
PUBLICATION_ALLOWED = False
EXECUTION_AUTHORITY = False


@dataclass(frozen=True, slots=True)
class GMGNObservation:
    source_id: str
    provider: str
    source_class: str
    observation_type: str
    observed_at: datetime
    payload: dict
    execution_authority: bool = False


def _decode_gmgn_bytes(value):
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if not isinstance(value, (bytes, bytearray)):
        return str(value)
    try:
        return bytes(value).decode("utf-8")
    except UnicodeDecodeError:
        return bytes(value).decode("utf-8", errors="replace")


def _json_from_stdout(value):
    text = _decode_gmgn_bytes(value).strip()
    if not text:
        raise RuntimeError("GMGN returned empty stdout")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        candidate = text[start:end + 1]
        try:
            return json.loads(candidate)
        except json.JSONDecodeError as exc:
            raise RuntimeError(
                "GMGN output contained text but no valid JSON object"
            ) from exc
    raise RuntimeError("GMGN output was not valid JSON")


def acquire_gmgn_solana_trending(interval="5m", limit=20, timeout_seconds=30.0):
    a = require_gmgn_admission()

    cmd = [
        a.cli_path,
        "market",
        "trending",
        "--chain",
        "sol",
        "--interval",
        str(interval),
        "--order-by",
        "volume",
        "--limit",
        str(int(limit)),
        "--raw",
    ]

    p = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=float(timeout_seconds),
        check=False,
    )

    stdout_text = _decode_gmgn_bytes(p.stdout)
    stderr_text = _decode_gmgn_bytes(p.stderr)

    if p.returncode != 0:
        detail = (stderr_text or stdout_text).strip()
        raise RuntimeError("GMGN trending failed: " + detail[:500])

    data = _json_from_stdout(p.stdout)

    if not isinstance(data, dict):
        raise RuntimeError("GMGN trending response root must be a JSON object")
    if data.get("code") != 0:
        raise RuntimeError(
            "GMGN trending returned non-success code: " + repr(data.get("code"))
        )

    return GMGNObservation(
        source_id="source.gmgn.solana.market.trending." + str(interval),
        provider="gmgn",
        source_class="market_intelligence",
        observation_type="gmgn_solana_trending",
        observed_at=datetime.now(timezone.utc),
        payload={
            "chain": "sol",
            "interval": str(interval),
            "limit": int(limit),
            "raw": data,
        },
        execution_authority=False,
    )
