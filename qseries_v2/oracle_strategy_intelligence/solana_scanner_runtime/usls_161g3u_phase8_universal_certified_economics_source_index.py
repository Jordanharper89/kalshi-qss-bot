from __future__ import annotations
import json,re
from pathlib import Path

FAMILIES=("PUMP_FUN","PUMP_SWAP","RAYDIUM_LAUNCHLAB","RAYDIUM_V4","RAYDIUM_CLMM",
"RAYDIUM_CPMM","METEORA_DBC","METEORA_DAMM_V1","METEORA_DAMM_V2","METEORA_DLMM",
"ORCA","MOONIT","BOOP_FUN","HEAVEN")
SIG=("trade_signature","signature")
MKT=("market_address","pool_address","pool","curve_address","curve","market_key")
PRICE=("effective_price","price","execution_price","price_usd","effective_output_per_input")
TIME=("observed_unix","trade_observed_unix","received_unix","scanner_observed_unix","block_time")

def _rows(x):
 if isinstance(x,list):return x
 if isinstance(x,dict):
  for k in ("rows","trades","events","normalized_rows","ready_rows","cases"):
   if isinstance(x.get(k),list):return x[k]
 return []

def _first(d,ks):
 if not isinstance(d,dict):return None
 for k in ks:
  if d.get(k) not in (None,""):return d.get(k)
 return None

def _family(r):
 f=str(_first(r,("family","venue","program_family","source_family")) or "").upper()
 if f=="METEORA_DAMM": return "METEORA_DAMM_V1"
 return f

def _inspect_file(p):
 try:
  if p.suffix==".json":
   rows=_rows(json.loads(p.read_text(encoding="utf-8",errors="ignore")))
  elif p.suffix==".jsonl":
   rows=[]
   for ln in p.read_text(encoding="utf-8",errors="ignore").splitlines()[:4000]:
    try:
     x=json.loads(ln)
     if isinstance(x,dict):rows.append(x)
    except Exception:pass
  else:return []
 except Exception:return []
 out=[]
 for r in rows[:5000]:
  fam=_family(r)
  if fam not in FAMILIES:continue
  out.append({"family":fam,"has_signature":_first(r,SIG) is not None,
   "has_market":_first(r,MKT) is not None,"has_price":_first(r,PRICE) is not None,
   "has_time":_first(r,TIME) is not None})
 return out

def run(root):
 root=Path(root);state=root/"runtime_state/solana_opportunities"
 per={f:{"files":0,"rows":0,"signature":0,"market":0,"price":0,"time":0,
         "fully_observable":0,"artifacts":[]} for f in FAMILIES}
 for p in list(state.rglob("*.json"))+list(state.rglob("*.jsonl")):
  rel=str(p.relative_to(root))
  rs=_inspect_file(p)
  if not rs:continue
  fams={}
  for r in rs:
   z=fams.setdefault(r["family"],{"rows":0,"signature":0,"market":0,"price":0,"time":0,"fully_observable":0})
   z["rows"]+=1
   for k in ("signature","market","price","time"):z[k]+=int(r["has_"+k])
   z["fully_observable"]+=int(all(r["has_"+k] for k in ("signature","market","price","time")))
  for fam,z in fams.items():
   q=per[fam];q["files"]+=1
   for k in ("rows","signature","market","price","time","fully_observable"):q[k]+=z[k]
   if z["fully_observable"]>0:q["artifacts"].append(rel)
 ready=[f for f,v in per.items() if v["fully_observable"]>0]
 return {"revision":"USLS_161G3U","family_count":len(FAMILIES),"family_support":per,
  "certified_economics_ready_family_count":len(ready),"certified_economics_ready_families":ready,
  "scope":"UNIVERSAL_14_FAMILY_CERTIFIED_ARTIFACT_INDEX_NO_NEW_DECODING",
  "next_boundary":"UNIVERSAL_LIVE_SIGNATURE_TO_CERTIFIED_ECONOMICS_BRIDGE",
  "profitability_claimed":False,"execution_authority":False,"read_only":True}

def write(root):
 d=run(root)
 p=Path(root)/"runtime_state/solana_opportunities/solana_scanner/phase8_universal_certified_economics_source_index.json"
 p.parent.mkdir(parents=True,exist_ok=True)
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8")
 return p,d
