from __future__ import annotations
import json,uuid
from pathlib import Path
from qseries_v2.oracle_adapters.independent.oad_314_solana_verified_forward_outcome_attribution import SolanaOutcomePendingCase
HORIZONS=(5,15,30,60,300,900)
def build(root):
 p=root/"runtime_state/solana_opportunities/live_token_pair_resolution.json";d=json.loads(p.read_text(encoding="utf-8"))
 if not d.get("matches"):raise RuntimeError("NO_RESOLVED_PAIR_MATCH")
 m=next((x for x in d["matches"] if x.get("pair_address")),None)
 if m is None:raise RuntimeError("NO_PAIR_ADDRESS_IN_RESOLVED_HISTORY")
 asset=d["asset_key"];cases=[]
 for h in HORIZONS:
  eid=f"osi:{asset}:{m['observation_id']}:{h}"
  cases.append(SolanaOutcomePendingCase(eid,asset,str(m["pair_address"]),m["observed_at"],tuple(),(m["observation_id"],),h))
 return {"revision":"OSI_061","asset_key":asset,"pair_address":str(m["pair_address"]),"anchor_observation_id":m["observation_id"],"cases":cases,"case_count":len(cases),"execution_authority":False}
