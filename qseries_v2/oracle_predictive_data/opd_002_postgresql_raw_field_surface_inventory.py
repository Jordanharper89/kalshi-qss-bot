
from pathlib import Path
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib, json

from qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect

SCAN_ROWS = 250000
TOP_GROUPS = 100
SAMPLE_PER_GROUP = 40

def _hash(x):
    return hashlib.sha256(
        json.dumps(x, sort_keys=True, separators=(",", ":"), default=str).encode()
    ).hexdigest()

def _flatten(obj, prefix="", out=None):
    out = out if out is not None else {}
    if isinstance(obj, dict):
        for k, v in obj.items():
            key = f"{prefix}.{k}" if prefix else str(k)
            if isinstance(v, dict):
                _flatten(v, key, out)
            elif isinstance(v, list):
                out[key] = f"LIST[{len(v)}]"
            else:
                out[key] = type(v).__name__
    return out

def inventory(root=None):
    root = Path(root or Path.cwd())
    with connect(root, autocommit=False) as c:
        with c.cursor() as q:
            q.execute("SET TRANSACTION READ ONLY")
            q.execute("SET LOCAL statement_timeout='30000ms'")
            q.execute("SELECT max(sequence_number) FROM public.oracle_canonical_observations")
            max_seq = int(q.fetchone()[0] or 0)
            lo = max(1, max_seq - SCAN_ROWS + 1)
            q.execute(
                "SELECT sequence_number, observed_at, source_id, observation_type, canonical_observation_json "
                "FROM public.oracle_canonical_observations "
                "WHERE sequence_number BETWEEN %s AND %s ORDER BY sequence_number",
                (lo, max_seq),
            )
            rows = q.fetchall() or []
        c.rollback()

    group_rows = defaultdict(list)
    first_last = {}
    for seq, observed_at, source_id, observation_type, obj in rows:
        key = (str(source_id), str(observation_type))
        if len(group_rows[key]) < SAMPLE_PER_GROUP:
            group_rows[key].append((int(seq), observed_at, obj))
        if key not in first_last:
            first_last[key] = [observed_at, observed_at, 0]
        first_last[key][1] = observed_at
        first_last[key][2] += 1

    groups = []
    for key, meta in first_last.items():
        source_id, observation_type = key
        path_types = defaultdict(Counter)
        for seq, observed_at, obj in group_rows[key]:
            for path, typ in _flatten(obj).items():
                path_types[path][typ] += 1
        fields = []
        for path, counts in sorted(path_types.items()):
            fields.append({
                "json_path": path,
                "observed_types": dict(counts),
                "sample_presence": sum(counts.values()),
            })
        groups.append({
            "source_id": source_id,
            "observation_type": observation_type,
            "rows_in_window": meta[2],
            "first_observed_at": meta[0],
            "last_observed_at": meta[1],
            "sampled_rows": len(group_rows[key]),
            "field_count": len(fields),
            "fields": fields,
        })

    groups.sort(key=lambda x: (-x["rows_in_window"], x["source_id"], x["observation_type"]))
    payload = {
        "schema_version": "OPD-002",
        "sequence_window": [lo, max_seq],
        "bounded_rows": len(rows),
        "group_count": len(groups),
        "groups": groups[:TOP_GROUPS],
        "read_only": True,
        "field_inventory_hash": _hash(groups[:TOP_GROUPS]),
        "probability_enabled": False,
        "direction_enabled": False,
        "publication_allowed": False,
        "execution_authority": False,
    }
    p = root / "runtime" / "predictive_data" / "opd_002_raw_field_surface_inventory.json"
    p.write_text(json.dumps(payload, sort_keys=True, indent=2, default=str), encoding="utf-8")
    return payload, p
