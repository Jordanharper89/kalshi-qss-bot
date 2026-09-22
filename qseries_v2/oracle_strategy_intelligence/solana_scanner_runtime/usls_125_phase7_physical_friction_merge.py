from __future__ import annotations
import json
from pathlib import Path

BASE="runtime_state/solana_opportunities/solana_scanner/phase7_friction_normalized_rows.json"
TX="runtime_state/solana_opportunities/solana_scanner/phase7_onchain_fee_latency_probe.json"
SRC="runtime_state/solana_opportunities/solana_scanner/phase7_source_native_friction_evidence.json"

def run(root):
 root=Path(root)
 b=json.loads((root/BASE).read_text(encoding="utf-8"))
 t=json.loads((root/TX).read_text(encoding="utf-8"))
 s=json.loads((root/SRC).read_text(encoding="utf-8"))
 txidx={x["trade_signature"]:x for x in t.get("rows",[])}
 sx={x["trade_signature"]:x for x in s.get("rows",[])}
 rows=[];fam={}
 for x in b.get("rows",[]):
  sig=x.get("trade_signature");a=txidx.get(sig,{});e=sx.get(sig,{})
  fee_lamports=a.get("network_fee_lamports")
  latency=a.get("observation_latency_seconds")
  liq=e.get("liquidity_evidence") or None
  pre=e.get("pre_trade_reserve_evidence") or None
  fee_native=e.get("fee_evidence") or None
  slippage_ready=bool(pre)
  row=dict(x)
  row.update({"network_fee_lamports":fee_lamports,
   "observation_latency_seconds":latency,
   "source_native_fee_evidence":fee_native,
   "liquidity_evidence":liq,
   "pre_trade_reference_evidence":pre,
   "slippage_model_ready":slippage_ready,
   "friction_state":"PHYSICAL_PARTIAL" if any(v is not None for v in (fee_lamports,latency,liq,fee_native,pre))
                    else "PHYSICAL_UNAVAILABLE"})
  rows.append(row)
  z=fam.setdefault(row["family"],{"rows":0,"partial":0,"slippage_ready":0})
  z["rows"]+=1;z["partial"]+=row["friction_state"]=="PHYSICAL_PARTIAL";z["slippage_ready"]+=slippage_ready
 return {"revision":"USLS_125","row_count":len(rows),"family_support":fam,"rows":rows,
  "network_fee_conversion_policy":"LAMPORTS_RETAINED_SEPARATELY_UNLESS_QUOTE_DENOMINATION_PROVEN",
  "next_boundary":"STRICT_EXECUTABLE_READINESS_GATE",
  "profitability_claimed":False,"execution_authority":False,"read_only":True}

def write(root):
 d=run(root)
 p=Path(root)/"runtime_state/solana_opportunities/solana_scanner/phase7_physical_friction_rows.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True,default=str),encoding="utf-8")
 return p,d
