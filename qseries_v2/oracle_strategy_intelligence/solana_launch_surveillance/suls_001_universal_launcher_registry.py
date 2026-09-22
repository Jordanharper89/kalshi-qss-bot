from __future__ import annotations
import json,re

REGISTRY=(
 {"family":"RAYDIUM_CPMM","aliases":("raydium_cpmm","cpmm")},
 {"family":"RAYDIUM_CLMM","aliases":("raydium_clmm","clmm")},
 {"family":"RAYDIUM_AMM","aliases":("raydium_amm","raydium_v4","raydium")},
 {"family":"METEORA_DLMM","aliases":("meteora_dlmm","dlmm")},
 {"family":"METEORA_DAMM","aliases":("meteora_damm","damm")},
 {"family":"METEORA","aliases":("meteora",)},
 {"family":"PUMPFUN","aliases":("pumpfun","pump.fun")},
 {"family":"PUMPSWAP","aliases":("pumpswap","pump_swap")},
 {"family":"MOONSHOT","aliases":("moonshot",)},
 {"family":"STONK_FUN","aliases":("stonk.fun","stonk_fun","stonkfun")},
 {"family":"BONK_FUN","aliases":("bonk.fun","bonk_fun","letsbonk","lets_bonk")},
 {"family":"ORCA_WHIRLPOOL","aliases":("orca_whirlpool","whirlpool","orca")},
)

def _norm(v):
 s=str(v or "").strip().lower()
 s=re.sub(r"[^a-z0-9]+","_",s).strip("_")
 return s

def classify(dex_id=None,program_hint=None,source_hint=None):
 vals={_norm(x) for x in (dex_id,program_hint,source_hint) if str(x or "").strip()}
 for row in REGISTRY:
  aliases={_norm(a) for a in row["aliases"]}
  if vals & aliases:return row["family"]
 return "UNKNOWN_PROGRAM"

def build():
 return {"revision":"SULS_001C",
  "registry":[{"family":x["family"],"aliases":list(x["aliases"]),
               "program_ids":[],"program_ids_physically_verified":False} for x in REGISTRY],
  "families":[x["family"] for x in REGISTRY]+["UNKNOWN_PROGRAM"],
  "unknown_program_admission":True,
  "observation_policy":"OBSERVE_FIRST_CLASSIFY_WHEN_KNOWN_NEVER_DROP_UNKNOWN",
  "program_ids_physically_verified":False,
  "execution_authority":False,"read_only":True}

def write(root):
 d=build()
 p=root/"runtime_state/solana_opportunities/launch_surveillance/launcher_registry.json"
 p.parent.mkdir(parents=True,exist_ok=True)
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8")
 return p,d
