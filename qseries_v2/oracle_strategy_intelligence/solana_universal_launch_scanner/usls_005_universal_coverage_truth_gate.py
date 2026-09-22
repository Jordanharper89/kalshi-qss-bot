from __future__ import annotations
import json
from pathlib import Path

TARGETS=(
 "PUMP_FUN","PUMP_SWAP","RAYDIUM_LAUNCHLAB","RAYDIUM_V4","RAYDIUM_CLMM","RAYDIUM_CPMM",
 "METEORA_DBC","METEORA_DAMM","METEORA_DLMM","METEORA_DYN",
 "BOOP_FUN","MOONIT","ORCA","HEAVEN","UNKNOWN_PROGRAM"
)

def gate(root):
 root=Path(root)
 base=root/"runtime_state/solana_opportunities/universal_launch_scanner"
 reg=json.loads((base/"family_registry.json").read_text(encoding="utf-8"))
 can=json.loads((base/"canonical_universal_birth_events.json").read_text(encoding="utf-8"))
 events=can.get("events") or []
 rows=[]
 for fam in TARGETS:
  r=reg["families"][fam]
  ev=[x for x in events if x.get("launcher_family")==fam or x.get("source_family")==fam]
  rows.append({"family":fam,"registry_status":r.get("status"),
   "program_id_count":len(r.get("program_ids") or []),
   "observed_births":len(ev),
   "identity_resolved":sum(1 for x in ev if x.get("token_address") and x.get("pair_address")),
   "live_scanner_certified":False if fam!="METEORA_DAMM" else bool(ev),
   "profitability_dataset_ready":False})
 known_ready=sum(1 for x in rows if x["live_scanner_certified"])
 universal_complete=all(x["live_scanner_certified"] for x in rows if x["family"]!="UNKNOWN_PROGRAM")
 return {"revision":"USLS_005","families":rows,
  "target_family_count":len(TARGETS),"live_certified_family_count":known_ready,
  "universal_scanner_complete":universal_complete,
  "unknown_fallback_active":reg.get("unknown_fallback_active") is True,
  "next_required_boundary":"USLS_006_UNIVERSAL_EVENT_SOURCE_ACTIVATION_AND_PROTOCOL_EXPANSION",
  "profitability_claimed":False,"execution_authority":False,"read_only":True}

def write(root):
 d=gate(root)
 p=Path(root)/"runtime_state/solana_opportunities/universal_launch_scanner/coverage_truth_gate.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8")
 return p,d
