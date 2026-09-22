from __future__ import annotations
import json,time,urllib.error,urllib.request
from pathlib import Path

RPC="https://api.mainnet-beta.solana.com"

def _tx(sig,max_attempts=5):
 delay=0.75
 last=None
 for attempt in range(1,max_attempts+1):
  body=json.dumps({"jsonrpc":"2.0","id":1,"method":"getTransaction",
   "params":[sig,{"encoding":"jsonParsed","commitment":"confirmed",
   "maxSupportedTransactionVersion":0}]}).encode()
  req=urllib.request.Request(RPC,data=body,headers={"Content-Type":"application/json"})
  try:
   with urllib.request.urlopen(req,timeout=20) as r:
    result=json.loads(r.read()).get("result")
   if result is not None:return result,None,attempt
   last="NULL_RESULT"
  except urllib.error.HTTPError as e:
   last=f"HTTP_{e.code}"
   if e.code!=429:return None,last,attempt
  except Exception as e:
   last=type(e).__name__+":"+str(e)
  if attempt<max_attempts:
   time.sleep(delay);delay=min(delay*2,6.0)
 return None,last,max_attempts

def hydrate(root):
 root=Path(root)
 base=root/"runtime_state/solana_opportunities/universal_launch_scanner"
 d=json.loads((base/"live_14_program_probe.json").read_text(encoding="utf-8"))

 # Choose one clean notification per observed family, newest first.
 chosen={}
 for x in reversed(d.get("notifications") or []):
  fam=x.get("family")
  sig=x.get("signature")
  if fam and sig and x.get("err") is None and fam not in chosen:
   chosen[fam]=x

 # A transaction may touch several subscribed programs. Hydrate it once,
 # then attach every family that observed that same signature.
 by_sig={}
 for fam,x in chosen.items():
  sig=x["signature"]
  row=by_sig.setdefault(sig,{"signature":sig,"slot":x.get("slot"),
   "observed_unix":x.get("observed_unix"),"families":[]})
  if fam not in row["families"]:row["families"].append(fam)

 rows=[]
 for i,row in enumerate(by_sig.values()):
  if i:time.sleep(0.45)
  tx,err,attempts=_tx(row["signature"])
  row.update({"hydrated":tx is not None,"error":err,"attempts":attempts,
   "raw_transaction":tx})
  rows.append(row)

 observed=sorted(chosen)
 covered=sorted({fam for r in rows if r["hydrated"] for fam in r["families"]})
 missing=sorted(set(observed)-set(covered))
 return {"revision":"USLS_012B","observed_family_count":len(observed),
  "observed_families":observed,"unique_signature_count":len(rows),
  "hydrated_signature_count":sum(1 for x in rows if x["hydrated"]),
  "hydrated_family_count":len(covered),"hydrated_families":covered,
  "missing_hydrated_families":missing,"rows":rows,
  "execution_authority":False,"read_only":True}

def write(root):
 d=hydrate(root)
 p=Path(root)/"runtime_state/solana_opportunities/universal_launch_scanner/live_multifamily_transactions.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8")
 return p,d
