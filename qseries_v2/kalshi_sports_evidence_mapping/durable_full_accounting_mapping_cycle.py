from pathlib import Path
from dataclasses import asdict
from datetime import datetime, timezone
from hashlib import sha256
import json, os, tempfile
from qseries_v2.kalshi_sports_evidence_mapping.supported_league_live_cohort import select_supported_live_cohort
from qseries_v2.kalshi_sports_evidence_mapping.structural_kalshi_event_identity import reconstruct_cohort
from qseries_v2.kalshi_sports_evidence_mapping.structural_osn_event_identity_resolver import resolve_cohort

READ_ONLY = True
EXECUTION_AUTHORITY = False
PROBABILITY_ENABLED = False
STATUSES = ("EXACT_BOUND","PARTIAL","AMBIGUOUS","SOURCE_GAP","UNSUPPORTED")

def _atomic_json(path, payload):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=path.name+".", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, sort_keys=True, default=str)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)

def run_full_cycle(root=None, universe_limit=1000, max_supported=40, timeout_seconds=15):
    root = Path(root or Path.cwd()).resolve()
    cohort = select_supported_live_cohort(
        root=root, universe_limit=universe_limit,
        max_supported=max_supported, timeout_seconds=timeout_seconds
    )
    identities = reconstruct_cohort(cohort)
    identity_rows = [asdict(x) for x in identities]
    bindings, events = resolve_cohort(identity_rows, root=root, timeout_seconds=timeout_seconds)
    binding_by_market = {b.market_ticker:b for b in bindings}
    observed = datetime.now(timezone.utc).isoformat()
    rows = []
    for identity in identities:
        b = binding_by_market.get(identity.market_ticker)
        status = b.status if b else "UNSUPPORTED"
        rows.append({
            "parent_ticker": identity.parent_ticker,
            "market_ticker": identity.market_ticker,
            "event_ticker": identity.event_ticker,
            "league": identity.league,
            "outcome_code": identity.outcome_code,
            "title": identity.title,
            "mapping_status": status,
            "provider": b.provider if b else None,
            "provider_event_id": b.provider_event_id if b else None,
            "home_team": b.home_team if b else None,
            "away_team": b.away_team if b else None,
            "scheduled_start": b.scheduled_start if b else None,
            "match_method": b.match_method if b else None,
            "observed_at": observed,
            "execution_authority": False,
        })
    counts = {s:sum(r["mapping_status"]==s for r in rows) for s in STATUSES}
    payload = {
        "schema_version":"KSEM-069",
        "observed_at":observed,
        "rows":rows,
        "counts":counts,
        "total_rows":len(rows),
        "accounted_rows":sum(counts.values()),
        "event_counts":{k:len(v) for k,v in events.items()},
        "probability_enabled":False,
        "execution_authority":False,
    }
    stable = dict(payload)
    stable.pop("observed_at", None)
    stable["rows"] = [{k:v for k,v in r.items() if k!="observed_at"} for r in rows]
    payload["content_hash"] = sha256(
        json.dumps(stable, sort_keys=True, separators=(",",":"), default=str).encode()
    ).hexdigest()
    path = root/"qseries_v2/kalshi_sports_evidence_mapping/state/ksem_live_mapping_state.json"
    _atomic_json(path, payload)
    return payload
