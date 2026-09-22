
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json

def _hash(x):
    return hashlib.sha256(
        json.dumps(x, sort_keys=True, separators=(",", ":"), default=str).encode()
    ).hexdigest()

def _event_key(x):
    d = x.get("detector")
    if d in {"OED-011", "OED-012"}:
        tickers = sorted([str(x.get("ticker_a")), str(x.get("ticker_b"))])
        seqs = sorted([int(x.get("sequence_a")), int(x.get("sequence_b"))])
        return ["PAIR_SEQUENCE", tickers, seqs]
    if d == "OED-013":
        fams = sorted([str(x.get("family_a")), str(x.get("family_b"))])
        return ["FAMILY_MINUTE", fams, int(x.get("minute_bin"))]
    if d == "OED-014":
        ticker = str(x.get("kalshi_first_ticker") or x.get("kalshi_last_ticker") or "")
        return ["BTC_REALITY_MINUTE", ticker, int(x.get("minute_bin"))]
    return ["UNKNOWN", str(x.get("candidate_id"))]

def freeze(root=None):
    root = Path(root or Path.cwd())
    src = root / "runtime" / "edge_discovery" / "oed_015_anomaly_candidate_registry.json"
    if not src.exists():
        raise FileNotFoundError(src)

    raw = json.loads(src.read_text(encoding="utf-8"))
    candidates = raw.get("candidates") or []
    source_hash = _hash(candidates)

    groups = {}
    for x in candidates:
        key = _event_key(x)
        kh = _hash(key)
        g = groups.setdefault(kh, {
            "event_id": kh,
            "event_key": key,
            "detectors": set(),
            "member_candidate_ids": [],
            "members": [],
        })
        g["detectors"].add(str(x.get("detector")))
        g["member_candidate_ids"].append(str(x.get("candidate_id")))
        g["members"].append(x)

    events = []
    for g in groups.values():
        g["detectors"] = sorted(g["detectors"])
        g["member_candidate_ids"] = sorted(set(g["member_candidate_ids"]))
        g["members"] = sorted(
            g["members"],
            key=lambda x: (str(x.get("detector")), str(x.get("candidate_id")))
        )
        g["member_count"] = len(g["members"])
        g["exact_sequence_identity"] = any(
            d in {"OED-011", "OED-012"} for d in g["detectors"]
        )
        g["exact_external_event_recoverable"] = "OED-014" in g["detectors"]
        g["legacy_outer_time_basis_only"] = (
            g["detectors"] == ["OED-013"]
        )
        events.append(g)

    events.sort(key=lambda x: x["event_id"])
    event_hash = _hash(events)

    payload = {
        "schema_version": "OED-016",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source_registry": str(src),
        "source_candidate_count": len(candidates),
        "source_registry_content_hash": source_hash,
        "normalized_event_count": len(events),
        "duplicate_members_collapsed": len(candidates) - len(events),
        "events": events,
        "event_population_hash": event_hash,
        "population_frozen": True,
        "event_time_invented": False,
        "edge_proven": False,
        "probability_enabled": False,
        "direction_enabled": False,
        "publication_allowed": False,
        "execution_authority": False,
    }

    dst = root / "runtime" / "edge_discovery" / "oed_016_normalized_event_population.json"
    dst.write_text(
        json.dumps(payload, sort_keys=True, indent=2, default=str),
        encoding="utf-8"
    )
    return payload, dst
