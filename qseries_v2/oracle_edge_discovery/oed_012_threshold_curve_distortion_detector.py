
from pathlib import Path
import re
from collections import defaultdict
from qseries_v2.oracle_edge_discovery.oed_011_cross_contract_inconsistency_detector import detect as base_detect

NUM_RE = re.compile(r'(?<![A-Z])(\d+(?:\.\d+)?)')

def _numeric_tokens(ticker):
    return [float(x) for x in NUM_RE.findall(str(ticker))]

def detect(root=None):
    base = base_detect(Path(root or Path.cwd()))
    out = []
    for x in base["anomalies"]:
        ta = _numeric_tokens(x["ticker_a"])
        tb = _numeric_tokens(x["ticker_b"])
        shared_numeric_structure = bool(ta and tb)
        out.append({
            **x,
            "ticker_a_numeric_tokens": ta,
            "ticker_b_numeric_tokens": tb,
            "threshold_structure_candidate": shared_numeric_structure,
            "monotonicity_violation_proven": False,
            "status": "OBSERVING" if shared_numeric_structure else "DISCOVERED",
        })

    candidates = [x for x in out if x["threshold_structure_candidate"]]
    candidates.sort(key=lambda x: x["absolute_price_gap"], reverse=True)
    return {
        "schema_version": "OED-012",
        "candidates": candidates,
        "candidate_count": len(candidates),
        "numeric_parser_only": True,
        "monotonicity_violation_proven": False,
        "edge_proven": False,
        "read_only": True,
    }
