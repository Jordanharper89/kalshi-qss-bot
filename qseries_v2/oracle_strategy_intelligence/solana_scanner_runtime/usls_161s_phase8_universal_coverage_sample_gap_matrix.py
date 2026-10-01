from __future__ import annotations
import json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_161k_phase8_universal_live_economics_producer_rebuild import contract

LEDGER="runtime_state/solana_opportunities/solana_scanner/phase8_prospective_oos_ledger.json"
LIVE="runtime_state/solana_opportunities/solana_scanner/phase8_strict_live_direct_economics.json"
REPLAY="runtime_state/solana_opportunities/solana_scanner/phase8_direct_decoder_replay_certification.json"
TARGET=("PUMP_FUN","PUMP_SWAP","RAYDIUM_LAUNCHLAB","RAYDIUM_V4","RAYDIUM_CLMM","RAYDIUM_CPMM",
"METEORA_DBC","METEORA_DAMM_V1","METEORA_DAMM_V2","METEORA_DLMM","ORCA","MOONIT","BOOP_FUN","HEAVEN")

def _load(root,p):
 q=Path(root)/p
 return {} if not q.exists() else json.loads(q.read_text(encoding="utf-8"))

def run(root):
 root=Path(root);led=_load(root,LEDGER);live=_load(root,LIVE);rep=_load(root,REPLAY);c=contract()
 lc={}; 
 for x in led.get("cases",[]):lc[x["family"]]=lc.get(x["family"],0)+1
 livefam=set((live.get("family_support") or {}).keys());repfam=set(rep.get("replay_ready_families") or [])
 supported=set(c["supported_families"]);pending=c["pending_families"]
 rows=[]
 for f in TARGET:
  reasons=[]
  if f not in supported:reasons.append(pending.get(f,"NO_DIRECT_DECODER"))
  if f in supported and f not in repfam:reasons.append("NO_REPLAY_CERTIFICATION_YET")
  if f in supported and f not in livefam:reasons.append("NO_STRICT_LIVE_ECONOMICS_OBSERVED_YET")
  if lc.get(f,0)==0:reasons.append("NO_PROSPECTIVE_OOS_CASE")
  rows.append({"family":f,"direct_decoder_supported":f in supported,"replay_ready":f in repfam,
   "strict_live_observed":f in livefam,"prospective_case_count":lc.get(f,0),
   "phase8_family_ready":f in supported and f in repfam and f in livefam and lc.get(f,0)>=5,
   "gaps":reasons})
 return {"revision":"USLS_161S","family_count":len(rows),"family_ready_count":sum(x["phase8_family_ready"] for x in rows),
  "rows":rows,"minimum_cases_per_family_for_initial_phase8_readiness":5,
  "next_boundary":"PHASE8_CHECKPOINT_NO_FALSE_UNIVERSAL_CERTIFICATION",
  "profitability_claimed":False,"execution_authority":False,"read_only":True}
def write(root):
 d=run(root);p=Path(root)/"runtime_state/solana_opportunities/solana_scanner/phase8_universal_coverage_sample_gap_matrix.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True,default=str),encoding="utf-8");return p,d
