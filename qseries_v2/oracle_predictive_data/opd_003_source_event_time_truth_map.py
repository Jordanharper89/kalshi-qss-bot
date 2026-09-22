
from pathlib import Path
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib, json

from qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect

SCAN_ROWS = 250000
CANDIDATE_PATHS = (
    "payload.message.ts",
    "payload.message.ts_ms",
    "payload.message.time",
    "payload.observation_payload.anchor_epoch",
    "payload.observation_payload.anchor_time",
    "payload.observation_payload.observed_at",
    "payload.event_time",
    "payload.timestamp",
    "observed_at",
    "acquired_at",
)

def _get(obj, path):
    cur = obj
    for part in path.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return None
        cur = cur[part]
    return cur

def _to_epoch(v, path):
    if v is None:
        return None
    try:
        if path.endswith("ts_ms"):
            return float(v) / 1000.0
        if path.endswith(".ts") or path.endswith("anchor_epoch"):
            return float(v)
        s = str(v).replace("Z", "+00:00")
        d = datetime.fromisoformat(s)
        if d.tzinfo is None:
            d = d.replace(tzinfo=timezone.utc)
        return d.timestamp()
    except Exception:
        return None

def _hash(x):
    return hashlib.sha256(
        json.dumps(x, sort_keys=True, separators=(",", ":"), default=str).encode()
    ).hexdigest()

def build(root=None):
    root = Path(root or Path.cwd())
    with connect(root, autocommit=False) as c:
        with c.cursor() as q:
            q.execute("SET TRANSACTION READ ONLY")
            q.execute("SET LOCAL statement_timeout='30000ms'")
            q.execute("SELECT max(sequence_number) FROM public.oracle_canonical_observations")
            hi = int(q.fetchone()[0] or 0)
            lo = max(1, hi - SCAN_ROWS + 1)
            q.execute(
                "SELECT sequence_number, observed_at, source_id, observation_type, canonical_observation_json "
                "FROM public.oracle_canonical_observations WHERE sequence_number BETWEEN %s AND %s "
                "ORDER BY sequence_number",
                (lo, hi),
            )
            rows = q.fetchall() or []
        c.rollback()

    by_group = defaultdict(lambda: {"rows":0, "path_counts":Counter(), "lags":defaultdict(list)})
    for seq, outer, sid, typ, obj in rows:
        key = (str(sid), str(typ))
        g = by_group[key]
        g["rows"] += 1
        outer_epoch = outer.timestamp()
        for path in CANDIDATE_PATHS:
            v = _get(obj, path)
            e = _to_epoch(v, path)
            if e is not None:
                g["path_counts"][path] += 1
                if path not in ("observed_at", "acquired_at"):
                    g["lags"][path].append(outer_epoch - e)

    groups = []
    for (sid, typ), g in by_group.items():
        ranked = sorted(g["path_counts"].items(), key=lambda x:(-x[1], CANDIDATE_PATHS.index(x[0])))
        selected = ranked[0][0] if ranked else "OUTER_OBSERVED_AT_ONLY"
        lag = g["lags"].get(selected, [])
        groups.append({
            "source_id": sid,
            "observation_type": typ,
            "rows": g["rows"],
            "candidate_event_time_paths": [{"path":p,"rows":n} for p,n in ranked],
            "selected_physical_event_time_path": selected,
            "selected_path_is_inner_source_time": selected != "OUTER_OBSERVED_AT_ONLY",
            "median_outer_minus_source_seconds": (
                sorted(lag)[len(lag)//2] if lag else None
            ),
            "max_abs_outer_minus_source_seconds": (
                max(abs(x) for x in lag) if lag else None
            ),
        })

    groups.sort(key=lambda x:(-x["rows"],x["source_id"],x["observation_type"]))
    payload = {
        "schema_version":"OPD-003",
        "sequence_window":[lo,hi],
        "groups":groups,
        "group_count":len(groups),
        "truth_map_hash":_hash(groups),
        "fallback_policy":"OUTER_OBSERVED_AT_ONLY_WHEN_NO_PHYSICAL_INNER_EVENT_TIME_EXISTS",
        "read_only":True,
        "probability_enabled":False,
        "direction_enabled":False,
        "publication_allowed":False,
        "execution_authority":False,
    }
    p=root/"runtime"/"predictive_data"/"opd_003_source_event_time_truth_map.json"
    p.write_text(json.dumps(payload,sort_keys=True,indent=2,default=str),encoding="utf-8")
    return payload,p
