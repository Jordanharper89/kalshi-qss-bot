from __future__ import annotations
import json
from pathlib import Path

CERTIFIED=("PUMP_FUN","PUMP_SWAP","RAYDIUM_LAUNCHLAB","RAYDIUM_V4","RAYDIUM_CLMM",
 "RAYDIUM_CPMM","METEORA_DBC","METEORA_DAMM_V1","METEORA_DAMM_V2","METEORA_DLMM",
 "ORCA","MOONIT","BOOP_FUN","HEAVEN")

def run(root):
 root=Path(root)
 reg=json.loads((root/"runtime_state/solana_opportunities/solana_scanner/cross_venue_path_adapter_registry.json").read_text(encoding="utf-8"))
 paths=json.loads((root/"runtime_state/solana_opportunities/solana_scanner/cross_venue_continuous_price_paths.json").read_text(encoding="utf-8"))
 regcov=reg.get("family_module_counts",{});pathcov=paths.get("family_path_counts",{})
 rows=[]
 for f in CERTIFIED:
  rows.append({"family":f,"decoder_pavement":regcov.get(f,0)>0,
   "physical_price_path":pathcov.get(f,0)>0,"path_count":pathcov.get(f,0)})
 missing_decoder=[x["family"] for x in rows if not x["decoder_pavement"]]
 missing_path=[x["family"] for x in rows if not x["physical_price_path"]]
 return {"revision":"USLS_116","families":rows,"certified_family_count":len(CERTIFIED),
  "decoder_covered_count":sum(x["decoder_pavement"] for x in rows),
  "path_covered_count":sum(x["physical_price_path"] for x in rows),
  "missing_decoder_families":missing_decoder,"missing_path_families":missing_path,
  "full_venue_path_coverage":not missing_decoder and not missing_path,
  "next_boundary":"PHASE6_FINAL_CERTIFICATION" if not missing_decoder and not missing_path
     else "REPAIR_MISSING_VENUE_PATH_ADAPTERS",
  "profitability_claimed":False,"execution_authority":False,"read_only":True}

def write(root):
 d=run(root)
 p=Path(root)/"runtime_state/solana_opportunities/solana_scanner/phase6_full_venue_coverage_gate.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8")
 return p,d
