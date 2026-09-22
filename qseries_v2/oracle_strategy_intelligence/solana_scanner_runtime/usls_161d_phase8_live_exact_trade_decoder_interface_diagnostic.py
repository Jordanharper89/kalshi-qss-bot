from __future__ import annotations
import ast,json
from pathlib import Path

FAMILIES={
 "PUMP_FUN":("pump_fun","pumpfun"),
 "PUMP_SWAP":("pump_swap","pumpswap"),
 "RAYDIUM_LAUNCHLAB":("raydium_launchlab","launchlab"),
 "RAYDIUM_V4":("raydium_v4",),
 "RAYDIUM_CLMM":("raydium_clmm",),
 "RAYDIUM_CPMM":("raydium_cpmm",),
 "METEORA_DBC":("meteora_dbc",),
 "METEORA_DAMM_V1":("meteora_damm_v1","damm_v1"),
 "METEORA_DAMM_V2":("meteora_damm_v2","damm_v2"),
 "METEORA_DLMM":("meteora_dlmm",),
 "ORCA":("orca",),
 "MOONIT":("moonit",),
 "BOOP_FUN":("boop_fun","boop"),
 "HEAVEN":("heaven",),
}

ROOTS=(
 "qseries_v2/oracle_strategy_intelligence/solana_universal_trade_tape",
 "qseries_v2/oracle_strategy_intelligence/solana_scanner_runtime",
 "qseries_v2/oracle_strategy_intelligence/solana_launch_surveillance",
)

WANTED=("decode","normal","material","extract","economic","trade")

def _functions(p):
 try:tree=ast.parse(p.read_text(encoding="utf-8",errors="ignore"))
 except Exception:return []
 out=[]
 for n in ast.walk(tree):
  if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)):
   name=n.name.lower()
   if any(w in name for w in WANTED):
    out.append({"name":n.name,"async":isinstance(n,ast.AsyncFunctionDef),
                "args":[a.arg for a in n.args.args]})
 return out

def run(root):
 root=Path(root);files=[]
 for rel in ROOTS:
  d=root/rel
  if d.exists():files.extend(d.rglob("*.py"))
 result={}
 for fam,terms in FAMILIES.items():
  hits=[]
  for p in files:
   s=str(p.relative_to(root)).lower()
   try:text=p.read_text(encoding="utf-8",errors="ignore").lower()
   except Exception:continue
   if not any(t in s or t in text for t in terms):continue
   funcs=_functions(p)
   if funcs:
    hits.append({"path":str(p.relative_to(root)),"functions":funcs})
  result[fam]=hits
 callable_fams=[f for f,h in result.items() if h]
 return {"revision":"USLS_161D","family_decoder_candidates":result,
  "family_count":len(result),"families_with_decoder_candidates":callable_fams,
  "decoder_candidate_family_count":len(callable_fams),
  "diagnostic_semantics":
   "STATIC_INTERFACE_DISCOVERY_ONLY_NO_DECODER_INVOCATION_NO_ECONOMIC_CLAIM",
  "next_boundary":(
   "LIVE_EXACT_TRADE_ECONOMICS_DISPATCHER"
   if len(callable_fams)>=2 else
   "REPAIR_OR_EXPOSE_DECODER_INTERFACES_BEFORE_LIVE_DISPATCH"),
  "profitability_claimed":False,"execution_authority":False,"read_only":True}

def write(root):
 d=run(root)
 p=Path(root)/"runtime_state/solana_opportunities/solana_scanner/phase8_live_exact_trade_decoder_interface_diagnostic.json"
 p.parent.mkdir(parents=True,exist_ok=True)
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8")
 return p,d
