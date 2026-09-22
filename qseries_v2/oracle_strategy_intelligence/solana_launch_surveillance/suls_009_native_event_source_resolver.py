from __future__ import annotations
import json
RANK=("logsSubscribe","programSubscribe","blockSubscribe","websocket","getBlock","getTransaction","getSignaturesForAddress")
def resolve(root):
 d=json.loads((root/"runtime_state/solana_opportunities/launch_surveillance/native_capability_audit.json").read_text(encoding="utf-8"));scored=[]
 for r in d.get("rows",[]):
  hits=r.get("hits",[]);score=sum((len(RANK)-i)*10 for i,x in enumerate(RANK) if x in hits)
  scored.append({"file":r["file"],"score":score,"hits":hits,"functions":r.get("functions",[])})
 scored.sort(key=lambda x:(-x["score"],x["file"]));best=scored[0] if scored else None
 return {"revision":"SULS_009","candidate_count":len(scored),"best_candidate":best,
 "native_event_candidate_found":bool(best and best["score"]>0),"execution_authority":False}
def write(root):
 d=resolve(root);p=root/"runtime_state/solana_opportunities/launch_surveillance/native_event_source_resolver.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
