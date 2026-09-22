from __future__ import annotations
import hashlib,json,time
from pathlib import Path
ASSET=("asset_key","mint","token_mint","pool_mint","base_mint","token_address","address")
TIME=("observed_at","timestamp","ts","created_at","block_time","blocktime","slot")
TYPE=("event_type","type","kind","event","instruction")
def _find(row:dict,names:tuple[str,...]):
 for k in names:
  if row.get(k) not in (None,""):return row.get(k)
 for v in row.values():
  if isinstance(v,dict):
   x=_find(v,names)
   if x not in (None,""):return x
 return None
def normalize(source_kind:str,source:str,row:dict)->dict|None:
 asset=_find(row,ASSET);ts=_find(row,TIME);etype=_find(row,TYPE)
 if asset in (None,"") or ts in (None,""):return None
 raw=json.dumps(row,sort_keys=True,default=str)
 eid=hashlib.sha256((source_kind+"|"+source+"|"+raw).encode()).hexdigest()
 return {"event_id":eid,"source_kind":source_kind,"source":source,"asset_key":str(asset),
  "observed_at":ts,"event_type":str(etype or "UNCLASSIFIED"),"payload":row,
  "execution_authority":False}
def normalize_batch(native:list,gmgn:list)->list[dict]:
 out=[]
 for kind,items in (("NATIVE_SOLANA",native),("GMGN",gmgn)):
  for x in items:
   e=normalize(kind,x["source"],x["row"])
   if e:out.append(e)
 return out
def write(root:Path,events:list[dict])->Path:
 p=root/"runtime_state/solana_opportunities/intake/normalized_events.jsonl";p.parent.mkdir(parents=True,exist_ok=True)
 seen=set()
 if p.is_file():
  for line in p.read_text(encoding="utf-8",errors="replace").splitlines()[-20000:]:
   try:seen.add(json.loads(line)["event_id"])
   except Exception:pass
 with p.open("a",encoding="utf-8") as f:
  for e in events:
   if e["event_id"] not in seen:f.write(json.dumps(e,sort_keys=True,default=str)+"\n");seen.add(e["event_id"])
 return p
