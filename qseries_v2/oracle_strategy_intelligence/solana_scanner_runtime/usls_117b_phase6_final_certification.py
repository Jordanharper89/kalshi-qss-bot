from __future__ import annotations
import json
from pathlib import Path

def _load(root,name):
 return json.loads((Path(root)/name).read_text(encoding="utf-8"))

def run(root):
 c=_load(root,"runtime_state/solana_opportunities/solana_scanner/phase6_universal_price_path_contract.json")
 p=_load(root,"runtime_state/solana_opportunities/solana_scanner/cross_venue_continuous_price_paths_repaired.json")
 g=_load(root,"runtime_state/solana_opportunities/solana_scanner/phase6_repaired_full_venue_coverage_gate.json")
 fam=p.get("family_path_counts",{})
 ok=(c.get("phase")==6 and
     c.get("path_contract",{}).get("continuous_between_horizons") and
     p.get("continuous_between_horizons") and
     len(fam)==14 and
     g.get("full_venue_path_coverage"))
 return {"revision":"USLS_117B","supersedes":"USLS_117_UNRUN_OLD_DESIGN",
  "phase":6,"path_count":p.get("path_count",0),
  "family_path_counts":fam,
  "family_path_count":len(fam),
  "full_venue_path_coverage":bool(g.get("full_venue_path_coverage")),
  "continuous_between_horizons":bool(p.get("continuous_between_horizons")),
  "phase6_physically_certified":bool(ok),
  "next_phase":"PHASE_7_EXECUTABLE_ENTRY_EXIT_MODELING" if ok else "PHASE_6_REPAIR_REQUIRED",
  "profitability_claimed":False,"execution_authority":False,"read_only":True}

def write(root):
 d=run(root)
 p=Path(root)/"runtime_state/solana_opportunities/solana_scanner/phase6_final_certification_v2.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8")
 return p,d
