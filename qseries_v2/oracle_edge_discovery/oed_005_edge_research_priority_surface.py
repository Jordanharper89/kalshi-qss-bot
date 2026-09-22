
from pathlib import Path
import json, math
from qseries_v2.oracle_edge_discovery.oed_003_kalshi_market_family_physical_inventory import inventory as market_inventory
from qseries_v2.oracle_edge_discovery.oed_004_independent_source_physical_inventory import inventory as source_inventory

def _log_score(v):
    return math.log10(max(1.0, float(v)))

def rank(root=None):
    root = Path(root or Path.cwd())
    markets = market_inventory(root)["families"]
    sources = source_inventory(root)["independent_source_candidates"]

    source_tokens = set()
    for src in sources:
        sid = src["source_id"].upper()
        for token in sid.replace(".","_").replace("-","_").split("_"):
            if len(token) >= 3:
                source_tokens.add(token)

    ranked = []
    for m in markets:
        family = m["family"]
        family_token = family[2:].upper() if family.startswith("KX") else family.upper()

        token_matches = sorted(
            t for t in source_tokens
            if t in family_token or family_token in t
        )

        trade_rows = int(m["types"].get("trade", 0))
        ticker_rows = int(m["types"].get("ticker", 0))
        density = _log_score(m["rows"])
        breadth = _log_score(m["contracts"])
        depth = _log_score(max(1.0, m["span_seconds"] / 60.0))
        path_richness = _log_score(trade_rows + ticker_rows)
        source_hint = min(2.0, 0.25 * len(token_matches))

        score = round(
            2.0*density +
            2.0*breadth +
            1.5*depth +
            1.0*path_richness +
            source_hint,
            6
        )

        ranked.append({
            "family": family,
            "research_priority_score": score,
            "rows": m["rows"],
            "contracts": m["contracts"],
            "span_seconds": m["span_seconds"],
            "trade_rows": trade_rows,
            "ticker_rows": ticker_rows,
            "source_namespace_token_hints": token_matches[:20],
            "source_hint_is_not_evidence_proof": True,
            "edge_proven": False,
        })

    ranked.sort(key=lambda x: x["research_priority_score"], reverse=True)

    state = {
        "schema_version": "OED-005",
        "families_ranked": len(ranked),
        "ranking": ranked,
        "edge_proven": False,
        "probability_enabled": False,
        "direction_enabled": False,
        "publication_allowed": False,
        "execution_authority": False,
    }

    dest = root / "runtime" / "edge_discovery"
    dest.mkdir(parents=True, exist_ok=True)
    (dest / "oed_005_edge_research_priority_surface.json").write_text(
        json.dumps(state, indent=2, default=str), encoding="utf-8"
    )
    return state
