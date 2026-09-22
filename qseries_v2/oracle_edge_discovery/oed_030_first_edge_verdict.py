
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json

def _h(x):
    return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(",",":"),default=str).encode()).hexdigest()

def build(root=None):
    root=Path(root or Path.cwd())
    v=json.loads((root/"runtime"/"edge_discovery"/"oed_028_strict_oos_behavior_validation.json").read_text())
    g=json.loads((root/"runtime"/"edge_discovery"/"oed_029_regime_and_profitability_reality_gate.json").read_text())

    tradable=[x for x in g["survivors"] if x["tradable_edge_certified"]]
    behavioral=[x for x in v["results"] if x["oos_behavior_survived_holm"]]

    if tradable:
        verdict="FIRST_REPEATABLE_PROFITABLE_EDGE_CERTIFIED"
    elif behavioral:
        verdict="BEHAVIORAL_SIGNAL_SURVIVED_BUT_NOT_YET_PROFITABLE_TRADABLE_EDGE"
    else:
        verdict="NO_EDGE_SURVIVED_STRICT_OUT_OF_SAMPLE_VALIDATION"

    payload={"schema_version":"OED-030","created_at":datetime.now(timezone.utc).isoformat(),
             "oos_rules_tested":v["tested_rules"],"raw_survivors":v["raw_survivors"],
             "holm_behavior_survivors":v["holm_survivors"],"regime_stable_survivors":g["regime_stable_count"],
             "profitability_proven_count":g["profitability_proven_count"],"tradable_edge_count":len(tradable),
             "verdict":verdict,"behavioral_survivors":behavioral,"certified_tradable_edges":tradable,
             "next_action":("FREEZE_AND_SHADOW_FORWARD_TEST_CERTIFIED_EDGE" if tradable else
                            "DO_NOT_TRADE; DEEPEN_ONLY_SURVIVING_BEHAVIORAL_SIGNAL_OR_OPEN_NEXT_EDGE_HUNT"),
             "probability_enabled":False,"direction_enabled":False,"publication_allowed":False,
             "execution_authority":False}
    payload["verdict_hash"]=_h({k:v for k,v in payload.items() if k!="created_at"})
    p=root/"runtime"/"edge_discovery"/"oed_030_first_edge_verdict.json"
    p.write_text(json.dumps(payload,sort_keys=True,indent=2),encoding="utf-8")
    return payload,p
