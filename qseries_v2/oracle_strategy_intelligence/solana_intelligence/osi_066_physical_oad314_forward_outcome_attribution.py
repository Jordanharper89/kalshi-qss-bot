from __future__ import annotations
import json
from dataclasses import asdict
from pathlib import Path
from qseries_v2.oracle_adapters.independent.oad_274_solana_multi_horizon_condition_windows import SolanaHistoricalObservation
from qseries_v2.oracle_adapters.independent.oad_314_solana_verified_forward_outcome_attribution import attribute_forward_outcomes
from qseries_v2.oracle_strategy_intelligence.solana_intelligence.osi_064_prospective_pending_case_set import build

def _obj(d):
 return SolanaHistoricalObservation(
  d["observation_id"],d["source_id"],d["observation_type"],d["observed_at"],
  d.get("sequence_number"),d.get("provider"),d.get("subject"),d["payload"]
 )

def run(root,tolerance_seconds=8.0):
 cases=build(root)
 data=json.loads((root/"runtime_state/solana_opportunities/outcomes/nonblocking_native_temporal_records.json").read_text(encoding="utf-8"))
 records=tuple(_obj(x) for x in data["records"])
 outcomes=tuple(attribute_forward_outcomes(cases,records,tolerance_seconds=tolerance_seconds))
 rows=[asdict(x) for x in outcomes];resolved=sorted({int(x["horizon_seconds"]) for x in rows})
 return {"revision":"OSI_066B","asset_key":cases[0].token_address,"record_count":len(records),
  "verified_outcomes":len(rows),"resolved_horizons":resolved,"outcomes":rows,"execution_authority":False}

def write(root):
 d=run(root);p=root/"runtime_state/solana_opportunities/outcomes/verified_forward_outcomes.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
