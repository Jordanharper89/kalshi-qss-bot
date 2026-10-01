from __future__ import annotations
import json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_161r_phase8_prospective_feature_outcome_empirical_learner import run as learn
from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_161k_phase8_universal_live_economics_producer_rebuild import contract

LEDGER="runtime_state/solana_opportunities/solana_scanner/phase8_prospective_oos_ledger.json"
LIVE1="runtime_state/solana_opportunities/solana_scanner/phase8_strict_live_direct_economics.json"
LIVE2="runtime_state/solana_opportunities/solana_scanner/phase8_balanced_live_economics.json"
REPLAY="runtime_state/solana_opportunities/solana_scanner/phase8_direct_decoder_replay_certification.json"
TARGET=("PUMP_FUN","PUMP_SWAP","RAYDIUM_LAUNCHLAB","RAYDIUM_V4","RAYDIUM_CLMM","RAYDIUM_CPMM","METEORA_DBC",
 "METEORA_DAMM_V1","METEORA_DAMM_V2","METEORA_DLMM","ORCA","MOONIT","BOOP_FUN","HEAVEN")

def _load(root,p):
 q=Path(root)/p
 return {} if not q.exists() else json.loads(q.read_text(encoding="utf-8"))

def run(root):
 root=Path(root);led=_load(root,LEDGER);rep=_load(root,REPLAY);a=_load(root,LIVE1);b=_load(root,LIVE2);c=contract()
 lc={}
 for x in led.get("cases",[]):lc[x["family"]]=lc.get(x["family"],0)+1
 live=set((a.get("family_support") or {}).keys())|set((b.get("family_support") or {}).keys())
 replay=set(rep.get("replay_ready_families") or []);supported=set(c["supported_families"]);rows=[]
 for f in TARGET:
  n=lc.get(f,0);gaps=[]
  if f not in supported:gaps.append(c["pending_families"].get(f,"DIRECT_DECODER_PENDING"))
  if f in supported and f not in replay:gaps.append("REPLAY_CERTIFICATION_PENDING")
  if f in supported and f not in live:gaps.append("STRICT_LIVE_OBSERVATION_PENDING")
  if n<5:gaps.append(f"PROSPECTIVE_OOS_CASES_{n}_OF_5")
  rows.append({"family":f,"decoder":f in supported,"replay":f in replay,"live":f in live,
   "prospective_case_count":n,"ready":f in supported and f in replay and f in live and n>=5,"gaps":gaps})
 learning=learn(root);ready=sum(x["ready"] for x in rows);total=len(led.get("cases",[]))
 complete=ready==14 and total>=70 and learning["learned_group_count"]>0
 return {"revision":"USLS_161Y","phase8_status":"PHYSICALLY_CERTIFIED" if complete else "IN_PROGRESS",
  "family_ready_count":ready,"target_family_count":14,"prospective_oos_case_count":total,
  "learned_group_count":learning["learned_group_count"],"rows":rows,"universal_phase8_complete":complete,
  "next_boundary":("PHASE9_CROSS_VENUE_LIFECYCLE_INTELLIGENCE" if complete else
   "CONTINUE_GAP_DRIVEN_OOS_ACCUMULATION_AND_ONLY_MISSING_FAMILY_REPAIRS"),
  "profitability_claimed":False,"execution_authority":False,"read_only":True}
def write(root):
 d=run(root);p=Path(root)/"runtime_state/solana_opportunities/solana_scanner/phase8_updated_learning_coverage_checkpoint.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True,default=str),encoding="utf-8");return p,d
