from __future__ import annotations
import json
from pathlib import Path
from qseries_v2.oracle_adapters.independent.oad_314_solana_verified_forward_outcome_attribution import SolanaOutcomePendingCase

HORIZONS=(5,15,30,60,300,900)

def build(root):
 d=json.loads((root/"runtime_state/solana_opportunities/outcomes/fresh_prospective_anchor.json").read_text(encoding="utf-8"))
 out=[]
 for h in HORIZONS:
  out.append(SolanaOutcomePendingCase(
   f"osi:{d['asset_key']}:{d['observation_id']}:{h}",
   d["asset_key"],
   d["pair_address"],
   d["observed_at"],
   tuple(),
   (d["observation_id"],),
   h,
  ))
 return tuple(out)
