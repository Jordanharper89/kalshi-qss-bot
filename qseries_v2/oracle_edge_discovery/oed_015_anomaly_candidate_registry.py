
from pathlib import Path
from datetime import datetime, timezone
import json, hashlib

from qseries_v2.oracle_edge_discovery.oed_011_cross_contract_inconsistency_detector import detect as d11
from qseries_v2.oracle_edge_discovery.oed_012_threshold_curve_distortion_detector import detect as d12
from qseries_v2.oracle_edge_discovery.oed_013_cross_family_reaction_divergence_detector import detect as d13
from qseries_v2.oracle_edge_discovery.oed_014_independent_reality_kalshi_divergence_detector import detect as d14

ALLOWED = {"DISCOVERED", "OBSERVING"}

def build_registry(root=None):
    root = Path(root or Path.cwd())
    rows = []

    for x in d11(root)["anomalies"]:
        rows.append({"detector": "OED-011", **x})
    for x in d12(root)["candidates"]:
        rows.append({"detector": "OED-012", **x})
    for x in d13(root)["divergences"]:
        rows.append({"detector": "OED-013", **x})
    for x in d14(root)["candidates"]:
        rows.append({"detector": "OED-014", **x})

    normalized = []
    seen = set()
    for x in rows:
        status = x.get("status", "DISCOVERED")
        if status not in ALLOWED:
            status = "DISCOVERED"
        body = json.dumps(x, default=str, sort_keys=True, separators=(",", ":"))
        cid = hashlib.sha256(body.encode()).hexdigest()
        if cid in seen:
            continue
        seen.add(cid)
        y = dict(x)
        y["candidate_id"] = cid
        y["status"] = status
        y["certified_edge"] = False
        normalized.append(y)

    payload = {
        "schema_version": "OED-015",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "candidate_count": len(normalized),
        "candidates": normalized,
        "allowed_statuses": sorted(ALLOWED),
        "rejected_candidate_retention_ready": True,
        "certified_edge_count": 0,
        "probability_enabled": False,
        "direction_enabled": False,
        "publication_allowed": False,
        "execution_authority": False,
    }

    p = root / "runtime" / "edge_discovery" / "oed_015_anomaly_candidate_registry.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(payload, default=str, sort_keys=True, indent=2), encoding="utf-8")
    return payload, p
