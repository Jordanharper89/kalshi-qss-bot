from __future__ import annotations
import json
from pathlib import Path

FAMILIES=("PUMP_FUN","PUMP_SWAP","RAYDIUM_LAUNCHLAB","RAYDIUM_V4","RAYDIUM_CLMM",
 "RAYDIUM_CPMM","METEORA_DBC","METEORA_DAMM_V1","METEORA_DAMM_V2","METEORA_DLMM",
 "ORCA","MOONIT","BOOP_FUN","HEAVEN")

def _load(root,name):
 p=Path(root)/name
 return json.loads(p.read_text(encoding="utf-8"))

def run(root):
 lat=_load(root,"runtime_state/solana_opportunities/solana_scanner/phase7_per_row_latency_recovery.json")
 dev=_load(root,"runtime_state/solana_opportunities/solana_scanner/phase7_pretrade_reference_execution_deviation.json")
 src=_load(root,"runtime_state/solana_opportunities/solana_scanner/phase7_source_native_friction_evidence.json")
 econ=_load(root,"runtime_state/solana_opportunities/solana_scanner/cross_venue_economic_rows_repaired.json")

 lf=lat.get("family_support",{});df=dev.get("family_support",{});sf=src.get("family_support",{})
 ef=econ.get("family_row_counts",{})
 rows=[]
 for f in FAMILIES:
  s=sf.get(f,{})
  row={"family":f,
   "economic_rows":ef.get(f,0),
   "latency_rows":lf.get(f,{}).get("latency",0),
   "pretrade_reference_rows":df.get(f,{}).get("bounded_reference",0),
   "fee_rows":s.get("fee",0),
   "liquidity_rows":s.get("liquidity",0)}
  row["missing_capabilities"]=[k for k,v in (
   ("ECONOMIC_PRICE",row["economic_rows"]),
   ("LATENCY",row["latency_rows"]),
   ("PRETRADE_REFERENCE",row["pretrade_reference_rows"]),
   ("FEE",row["fee_rows"]),
   ("LIQUIDITY",row["liquidity_rows"])) if v<=0]
  row["fully_supported"]=not row["missing_capabilities"]
  rows.append(row)
 return {"revision":"USLS_133","phase":7,"families":rows,
  "fully_supported_family_count":sum(x["fully_supported"] for x in rows),
  "fully_supported_families":[x["family"] for x in rows if x["fully_supported"]],
  "gap_families":[x["family"] for x in rows if not x["fully_supported"]],
  "next_boundary":"CROSS_VENUE_NATIVE_FRICTION_EXTRACTION",
  "profitability_claimed":False,"execution_authority":False,"read_only":True}

def write(root):
 d=run(root)
 p=Path(root)/"runtime_state/solana_opportunities/solana_scanner/phase7_cross_venue_executable_gap_matrix.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8")
 return p,d
