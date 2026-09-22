from __future__ import annotations
import ast,json,re
from pathlib import Path

SEARCH_DIRS=(
 "qseries_v2/oracle_strategy_intelligence/solana_launch_surveillance",
 "qseries_v2/oracle_strategy_intelligence/solana_universal_launch_scanner",
)
PROGRAM_TERMS={
 "PUMP_FUN":"6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P",
 "PUMP_SWAP":"pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA",
 "RAYDIUM_LAUNCHLAB":"LanMV9sAd7wArD4vJFi2qDdfnVhFxYSUg6eADduJ3uj",
 "RAYDIUM_V4":"675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8",
 "RAYDIUM_CLMM":"CAMMCzo5YL8w4VFF8KVHrK22GGUsp5VTaW7grrKgrWqK",
 "RAYDIUM_CPMM":"CPMMoo8L3F4NbTegBCKVNunggL7H1ZpdTHKxQB5qKP1C",
 "METEORA_DBC":"dbcij3LWUppWqq96dh6gJWwBifmcGfLSB5D4DuSMaqN",
 "METEORA_DAMM_V2":"cpamdpZCGKUy5JxQXB4dcpGPiikHawvSWAd6mEn1sGG",
 "METEORA_DLMM":"LBUZKhRxPF3XUpBCjp4YzTKgLccjZhTSDM9YuVaPwxo",
 "METEORA_DAMM_V1":"Eo7WjKq67rjJQSZxS6z3YkapzY3eMj6Xy8X5EQVn5UaB",
 "ORCA":"whirLbMiicVdio4qvUfM5KAg6Ct8VwpYzGff3uctyCc",
 "MOONIT":"MoonCVVNZFSYkqNXP6bxHLPL6QQJiMagDL3qcqUQTrG",
 "BOOP_FUN":"boop8hVGQGqehUK2iVEMEnMrL5RbjywRzHKBmBE7ry4",
 "HEAVEN":"HEAVENoP2qxoeuF8Dj2oT1GHEnu49U5mJYkdeC8BAX2o",
}
KEYWORDS=("birth","create","initialize","pool","launch","migration","curve")
PUMP_CREATE_V2="d6904cec5f8b31b4"

def _funcs(src):
 try:t=ast.parse(src)
 except Exception:return []
 out=[]
 for n in ast.walk(t):
  if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)):
   out.append({"name":n.name,"async":isinstance(n,ast.AsyncFunctionDef),
    "args":[a.arg for a in n.args.args]})
 return out

def run(root):
 root=Path(root);rows=[]
 for rel in SEARCH_DIRS:
  base=root/rel
  if not base.exists():continue
  for p in sorted(base.rglob("*.py")):
   src=p.read_text(encoding="utf-8",errors="ignore")
   low=src.lower()
   families=[name for name,pid in PROGRAM_TERMS.items() if pid in src]
   pump_disc=PUMP_CREATE_V2 in low.replace("0x","")
   kw=sorted({k for k in KEYWORDS if k in low})
   funcs=[f for f in _funcs(src) if any(k in f["name"].lower() for k in KEYWORDS)]
   if families or pump_disc or funcs:
    rows.append({"path":str(p.relative_to(root)),"families":families,
     "pump_create_v2_discriminator_present":pump_disc,
     "keywords":kw,"candidate_functions":funcs})
 family_map={k:[] for k in PROGRAM_TERMS}
 for r in rows:
  for f in r["families"]:family_map[f].append(r["path"])
 exact_candidates=[r for r in rows if r["candidate_functions"] or r["pump_create_v2_discriminator_present"]]
 return {"revision":"USLS_106V","candidate_module_count":len(rows),
  "exact_candidate_module_count":len(exact_candidates),
  "family_module_counts":{k:len(v) for k,v in family_map.items()},
  "family_modules":family_map,"candidates":exact_candidates,
  "next_boundary":"EXACT_BIRTH_DECODER_DISPATCH_FROM_DISCOVERED_INTERFACES",
  "certification_claimed":False,"execution_authority":False,"read_only":True}

def write(root):
 d=run(root)
 p=Path(root)/"runtime_state/solana_opportunities/solana_scanner/phase5_exact_birth_decoder_interface_census.json"
 p.parent.mkdir(parents=True,exist_ok=True)
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8")
 return p,d
