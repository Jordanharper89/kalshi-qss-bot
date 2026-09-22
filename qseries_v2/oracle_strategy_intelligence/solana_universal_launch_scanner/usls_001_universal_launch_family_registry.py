from __future__ import annotations
import json,re
from pathlib import Path

TARGETS=(
 "PUMP_FUN","PUMP_SWAP","RAYDIUM_LAUNCHLAB","RAYDIUM_V4","RAYDIUM_CLMM","RAYDIUM_CPMM",
 "METEORA_DBC","METEORA_DAMM","METEORA_DLMM","METEORA_DYN",
 "BOOP_FUN","MOONIT","ORCA","HEAVEN","UNKNOWN_PROGRAM"
)

CERTIFIED={
 "METEORA_DBC":{"program_ids":["dbcij3LWUppWqq96dh6gJWwBifmcGfLSB5D4DuSMaqN"],
                "status":"PHYSICALLY_CERTIFIED_EXISTING_SULS"},
 "METEORA_DAMM":{"program_ids":["cpamdpZCGKUy5JxQXB4dcpGPiikHawvSWAd6mEn1sGG"],
                 "status":"PHYSICALLY_CERTIFIED_EXISTING_SULS"},
}

ALIASES={
 "PUMP_FUN":("pump.fun","pumpfun","pump_fun"),
 "PUMP_SWAP":("pumpswap","pump.swap","pump_swap"),
 "RAYDIUM_LAUNCHLAB":("launchlab","raydium_launchlab"),
 "RAYDIUM_V4":("raydium_v4","raydium v4"),
 "RAYDIUM_CLMM":("raydium_clmm","clmm"),
 "RAYDIUM_CPMM":("raydium_cpmm","cpmm"),
 "METEORA_DBC":("meteora_dbc","dbcij3"),
 "METEORA_DAMM":("meteora_damm","damm v2","cpamdp"),
 "METEORA_DLMM":("meteora_dlmm","dlmm"),
 "METEORA_DYN":("meteora_dyn","meteora dyn"),
 "BOOP_FUN":("boop.fun","boop_fun"),
 "MOONIT":("moonit","moonshot"),
 "ORCA":("orca","whirlpool"),
 "HEAVEN":("heaven",),
}

BASE58=re.compile(r"\b[1-9A-HJ-NP-Za-km-z]{32,44}\b")

def build_registry(root):
 root=Path(root).resolve()
 rows={}
 for family in TARGETS:
  base=CERTIFIED.get(family,{"program_ids":[],"status":"UNVERIFIED"})
  rows[family]={"family":family,"program_ids":list(base["program_ids"]),
                "status":base["status"],"evidence_paths":[]}
 rows["UNKNOWN_PROGRAM"]["status"]="ACTIVE_FALLBACK_NEVER_DROP"

 search_roots=[root/"qseries_v2",root/"runtime_state"]
 for p0 in search_roots:
  if not p0.exists(): continue
  for p in p0.rglob("*"):
   if not p.is_file() or p.suffix.lower() not in (".py",".json",".txt"): continue
   try:text=p.read_text(encoding="utf-8",errors="ignore")
   except Exception:continue
   low=text.lower()
   for fam,aliases in ALIASES.items():
    if any(a in low for a in aliases):
     rel=str(p.relative_to(root)).replace("\\","/")
     if rel not in rows[fam]["evidence_paths"]:
      rows[fam]["evidence_paths"].append(rel)

 return {"revision":"USLS_001","families":rows,
         "target_count":len(TARGETS),
         "verified_family_count":sum(1 for x in rows.values() if x["program_ids"]),
         "unknown_fallback_active":True,"execution_authority":False,"read_only":True}

def write(root):
 d=build_registry(root)
 p=Path(root)/"runtime_state/solana_opportunities/universal_launch_scanner/family_registry.json"
 p.parent.mkdir(parents=True,exist_ok=True)
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8")
 return p,d
