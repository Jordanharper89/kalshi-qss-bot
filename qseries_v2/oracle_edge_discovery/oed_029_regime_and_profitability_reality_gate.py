
from pathlib import Path
from collections import defaultdict,Counter
from datetime import datetime,timezone
import hashlib,json

def _h(x):
    return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(",",":"),default=str).encode()).hexdigest()

def build(root=None):
    root=Path(root or Path.cwd())
    pop=json.loads((root/"runtime"/"edge_discovery"/"oed_026_chronological_validation_population.json").read_text())
    val=json.loads((root/"runtime"/"edge_discovery"/"oed_028_strict_oos_behavior_validation.json").read_text())
    cmap={x["condition_key"]:x for x in pop["conditions"]}
    rows=[]
    for r in val["results"]:
        if not r["oos_behavior_survived_holm"]:
            continue
        c=cmap[r["condition_key"]]
        test=c["test_rows"]
        by_day=defaultdict(list)
        for x in test: by_day[x["calendar_day_utc"]].append(x)
        day_stats=[]
        for d,rs in sorted(by_day.items()):
            hit=sum(x["behavior"]==r["locked_prediction"] for x in rs)
            day_stats.append({"day":d,"n":len(rs),"hit_rate":hit/len(rs)})
        stable_days=sum(x["hit_rate"]>r["train_family_majority_baseline"] for x in day_stats)
        regime_stable=len(day_stats)>=2 and stable_days>=2 and stable_days/len(day_stats)>=0.67

        # Current dispersion rows describe pair behavior, but do not encode a certified,
        # semantically valid long/short portfolio with fees/slippage. Never manufacture P&L.
        trade_mapping_available=False
        profitability_after_costs_proven=False
        reason="NO_CERTIFIED_TRADE_MAPPING_FROM_BEHAVIOR_CLASS_TO_EXECUTABLE_PAIR_PNL"
        rows.append({**r,"test_day_count":len(day_stats),"day_stats":day_stats,
                     "regime_stable":regime_stable,"trade_mapping_available":trade_mapping_available,
                     "profitability_after_costs_proven":profitability_after_costs_proven,
                     "profitability_hold_reason":reason,"tradable_edge_certified":False})
    payload={"schema_version":"OED-029","created_at":datetime.now(timezone.utc).isoformat(),
             "source_results_hash":val["results_hash"],"holm_behavior_survivors":len(rows),"survivors":rows,
             "regime_stable_count":sum(x["regime_stable"] for x in rows),
             "profitability_proven_count":sum(x["profitability_after_costs_proven"] for x in rows),
             "tradable_edge_count":sum(x["tradable_edge_certified"] for x in rows),
             "semantic_trade_mapping_required":True,"fees_slippage_required":True,"gate_hash":_h(rows),
             "edge_proven":False,"probability_enabled":False,"direction_enabled":False,
             "publication_allowed":False,"execution_authority":False}
    p=root/"runtime"/"edge_discovery"/"oed_029_regime_and_profitability_reality_gate.json"
    p.write_text(json.dumps(payload,sort_keys=True,indent=2),encoding="utf-8")
    return payload,p
