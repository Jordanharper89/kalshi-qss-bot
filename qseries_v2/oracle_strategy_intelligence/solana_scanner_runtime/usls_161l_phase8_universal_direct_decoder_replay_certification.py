from __future__ import annotations
import json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_161k_phase8_universal_live_economics_producer_rebuild import decode_live_trade,contract

SOURCES=(
 ("RAYDIUM_V4","raydium_exact_swap_instructions.json"),
 ("RAYDIUM_CLMM","raydium_exact_swap_instructions.json"),
 ("RAYDIUM_CPMM","raydium_exact_swap_instructions.json"),
 ("RAYDIUM_LAUNCHLAB","launchlab_deep_trade_census.json"),
 ("METEORA_DBC","meteora_orca_exact_swap_instructions.json"),
 ("METEORA_DAMM_V2","meteora_orca_exact_swap_instructions.json"),
 ("METEORA_DLMM","meteora_orca_exact_swap_instructions.json"),
 ("ORCA","meteora_orca_exact_swap_instructions.json"),
 ("MOONIT","remaining_venue_exact_trade_census.json"),
 ("BOOP_FUN","remaining_venue_exact_trade_census.json"),
 ("HEAVEN","remaining_venue_exact_trade_census.json"),
)

def run(root):
 root=Path(root);base=root/"runtime_state/solana_opportunities/universal_trade_tape";by={};samples=[]
 for fam,name in SOURCES:
  p=base/name
  if not p.exists():by[fam]={"source_missing":True,"attempted":0,"decoded":0};continue
  d=json.loads(p.read_text(encoding="utf-8"));rows=d.get("rows") or [];attempted=decoded=0
  for x in rows:
   venue=str(x.get("venue") or fam).upper()
   if fam=="METEORA_DAMM_V2" and venue not in ("METEORA_DAMM","METEORA_DAMM_V2"):continue
   if fam!="METEORA_DAMM_V2" and venue!=fam and name!="launchlab_deep_trade_census.json":continue
   tx=x.get("transaction");sig=x.get("signature")
   if not isinstance(tx,dict) or not sig:continue
   attempted+=1;out=decode_live_trade(fam,sig,tx,x.get("observed_unix") or tx.get("blockTime"))
   strict=[z for z in out if z.get("trade_signature")==sig and z.get("market_address") and z.get("strict_live_provenance")]
   decoded+=len(strict)
   if strict and len(samples)<20:samples.append(strict[0])
   if attempted>=12:break
  by[fam]={"source_missing":False,"attempted":attempted,"decoded":decoded}
 ready=sorted(f for f,v in by.items() if v.get("decoded",0)>0)
 return {"revision":"USLS_161L","family_support":by,"replay_ready_families":ready,
  "replay_ready_family_count":len(ready),"sample_rows":samples,
  "pending_families":contract()["pending_families"],
  "next_boundary":"BOUNDED_LIVE_DIRECT_DECODER_GATE",
  "profitability_claimed":False,"execution_authority":False,"read_only":True}
def write(root):
 d=run(root);p=Path(root)/"runtime_state/solana_opportunities/solana_scanner/phase8_direct_decoder_replay_certification.json"
 p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,indent=2,sort_keys=True,default=str),encoding="utf-8");return p,d
