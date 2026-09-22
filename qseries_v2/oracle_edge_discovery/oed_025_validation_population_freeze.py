
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib
def _h(x): return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(",",":"),default=str).encode()).hexdigest()
def build(root=None):
    root=Path(root or Path.cwd())
    s=json.loads((root/"runtime"/"edge_discovery"/"oed_024_candidate_condition_scoreboard.json").read_text())
    eligible=[x for x in s["scoreboard"] if int(x["sample_size"])>=20]
    eligible.sort(key=lambda x:(-x["raw_lift_over_baseline"],-x["sample_size"],x["family_key"]))
    y={"schema_version":"OED-025","created_at":datetime.now(timezone.utc).isoformat(),
       "source_scoreboard_hash":s["scoreboard_hash"],"validation_candidates":eligible,
       "validation_candidate_count":len(eligible),"minimum_discovery_sample":20,"freeze_hash":_h(eligible),
       "population_frozen_for_next_phase":True,"next_phase":"OED-026..030_STRICT_OUT_OF_SAMPLE_EDGE_VALIDATION",
       "required_next":["temporal_holdout","contract_day_isolation","embargo","baseline_comparison",
                        "multiple_testing_control","regime_stability","profitability_after_costs"],
       "predictive_model_fit_allowed":False,"certified_edge_count":0,"edge_proven":False,
       "probability_enabled":False,"direction_enabled":False,"publication_allowed":False,"execution_authority":False}
    p=root/"runtime"/"edge_discovery"/"oed_025_validation_population_freeze.json"
    p.write_text(json.dumps(y,sort_keys=True,indent=2),encoding="utf-8"); return y,p
