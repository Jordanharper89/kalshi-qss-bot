from __future__ import annotations
def join(features:list[dict],outcomes:list[dict])->dict:
 by_id={str(x.get("observation_id") or x.get("case_id") or x.get("asset_key")):x for x in outcomes}
 rows=[]
 for f in features:
  key=str(f.get("observation_id") or f.get("case_id") or f.get("asset_key"))
  o=by_id.get(key)
  if not o:continue
  rows.append({"case_id":key,"observed_at":f.get("observed_at"),"features":f.get("features",{}),"outcomes":o.get("outcomes",o)})
 return {"revision":"OSI_051","cases":rows,"case_count":len(rows),"execution_authority":False,"read_only":True}
