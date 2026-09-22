from __future__ import annotations
import ast,json
from pathlib import Path

FAMILIES=("PUMP_FUN","PUMP_SWAP","RAYDIUM_LAUNCHLAB","RAYDIUM_V4","RAYDIUM_CLMM",
 "RAYDIUM_CPMM","METEORA_DBC","METEORA_DAMM_V1","METEORA_DAMM_V2",
 "METEORA_DLMM","ORCA","MOONIT","BOOP_FUN","HEAVEN")

ROOTS=(
 "qseries_v2/oracle_strategy_intelligence/solana_universal_trade_tape",
 "qseries_v2/oracle_strategy_intelligence/solana_universal_launch_scanner",
 "qseries_v2/oracle_strategy_intelligence/solana_launch_surveillance",
)

def _funcs(src):
 try:t=ast.parse(src)
 except Exception:return []
 out=[]
 for n in ast.walk(t):
  if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)):
   name=n.name.lower()
   if any(k in name for k in ("decode","normalize","trade","economic","amount","price")):
    out.append({"name":n.name,"args":[a.arg for a in n.args.args],
                "async":isinstance(n,ast.AsyncFunctionDef)})
 return out

def run(root):
 root=Path(root);mods=[]
 for rel in ROOTS:
  b=root/rel
  if not b.exists():continue
  for p in b.rglob("*.py"):
   src=p.read_text(encoding="utf-8",errors="ignore");up=src.upper()
   fam=[f for f in FAMILIES if f in up or f.replace("_","") in up.replace("_","")]
   fs=_funcs(src)
   if fam and fs:
    mods.append({"path":str(p.relative_to(root)),"families":fam,"functions":fs})
 family={f:[] for f in FAMILIES}
 for m in mods:
  for f in m["families"]:family[f].append(m["path"])
 return {"revision":"USLS_111","family_module_counts":{k:len(v) for k,v in family.items()},
  "family_modules":family,"candidate_modules":mods,
  "universal_adapter_contract":{
    "required_output":["family","token_address","market_address","trade_signature","trade_slot",
      "trade_observed_unix","side","base_quantity","quote_quantity","effective_price"],
    "unknown_policy":"RETAIN","quote_asset_policy":"AGNOSTIC"},
  "next_boundary":"WIRE_CERTIFIED_VENUE_ECONOMIC_DECODERS_TO_UNIVERSAL_PATH_SCHEMA",
  "profitability_claimed":False,"execution_authority":False,"read_only":True}

def write(root):
 d=run(root)
 p=Path(root)/"runtime_state/solana_opportunities/solana_scanner/cross_venue_path_adapter_registry.json"
 p.parent.mkdir(parents=True,exist_ok=True)
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8")
 return p,d
