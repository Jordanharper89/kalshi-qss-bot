from __future__ import annotations
import json,re
from pathlib import Path

def extract(root):
 root=Path(root);candidates=[]
 for p in (root/"qseries_v2").rglob("*.py"):
  try:s=p.read_text(encoding="utf-8",errors="ignore")
  except Exception:continue
  score=0
  for term,w in (("logsSubscribe",5),("websocket",2),("wss://",2),
                 ("dbcij3LW",2),("cpamdpZC",2),("event_driven",1)):
   if term.lower() in s.lower():score+=w
  if score>=5:
   lines=s.splitlines();hits=[]
   for i,line in enumerate(lines,1):
    if any(t.lower() in line.lower() for t in ("logssubscribe","websocket","wss://","dbcij3lw","cpamdpzc")):
     hits.append({"line":i,"text":line[:500]})
   candidates.append({"path":str(p.relative_to(root)).replace("\\","/"),
    "score":score,"line_count":len(lines),"hits":hits[:80]})
 candidates.sort(key=lambda x:(-x["score"],x["path"]))
 return {"revision":"USLS_009","candidate_count":len(candidates),"candidates":candidates[:20],
  "best_candidate":candidates[0] if candidates else None,
  "execution_authority":False,"read_only":True}

def write(root):
 d=extract(root);p=Path(root)/"runtime_state/solana_opportunities/universal_launch_scanner/existing_websocket_boundary.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
