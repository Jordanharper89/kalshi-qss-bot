from __future__ import annotations
import json,os,time,urllib.request
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_060_launchlab_official_trade_contract import PROGRAM,classify
ALPH="123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
RPC=os.environ.get("SOLANA_RPC_URL","https://api.mainnet.solana.com")

def b58d(s):
 n=0
 for c in s:n=n*58+ALPH.index(c)
 b=n.to_bytes((n.bit_length()+7)//8,"big") if n else b""
 return b"\0"*(len(s)-len(s.lstrip("1")))+b

def rpc(method,params,retries=6):
 payload=json.dumps({"jsonrpc":"2.0","id":1,"method":method,"params":params}).encode();last=None
 for n in range(retries):
  try:
   req=urllib.request.Request(RPC,data=payload,headers={"Content-Type":"application/json","User-Agent":"qseries-oracle-usls061"})
   with urllib.request.urlopen(req,timeout=20) as r:return json.loads(r.read()).get("result")
  except Exception as e:
   last=e;time.sleep(min(1.5*(n+1),6))
 return None

def signatures(limit=250):
 out=[];before=None
 while len(out)<limit:
  opts={"limit":min(100,limit-len(out)),"commitment":"confirmed"}
  if before:opts["before"]=before
  page=rpc("getSignaturesForAddress",[PROGRAM,opts]) or []
  good=[x["signature"] for x in page if x.get("signature") and x.get("err") is None]
  out+=good
  if len(page)<opts["limit"] or not page:break
  before=page[-1].get("signature");time.sleep(.35)
 return out

def keys(tx):
 ks=(((tx or {}).get("transaction") or {}).get("message") or {}).get("accountKeys") or []
 return [x.get("pubkey") if isinstance(x,dict) else x for x in ks]

def all_ix(tx):
 msg=((tx or {}).get("transaction") or {}).get("message") or {};out=[]
 for i,ix in enumerate(msg.get("instructions") or []):out.append(("top",i,ix))
 for g in ((tx or {}).get("meta") or {}).get("innerInstructions") or []:
  for i,ix in enumerate(g.get("instructions") or []):out.append((f"inner:{g.get('index')}",i,ix))
 return out

def hydrate(sig):
 return rpc("getTransaction",[sig,{"encoding":"jsonParsed","commitment":"confirmed","maxSupportedTransactionVersion":0}])

def build(root):
 sigs=signatures();rows=[];hydrated=0
 for n,s in enumerate(sigs):
  tx=hydrate(s)
  if not tx:continue
  hydrated+=1;ks=keys(tx)
  for level,ordinal,ix in all_ix(tx):
   pid=ix.get("programId")
   if not pid and isinstance(ix.get("programIdIndex"),int) and ix["programIdIndex"]<len(ks):pid=ks[ix["programIdIndex"]]
   if pid!=PROGRAM or not ix.get("data"):continue
   c=classify(b58d(ix["data"]))
   if c["is_exact_trade"]:
    ac=ix.get("accounts") or [];ac=[ks[a] if isinstance(a,int) and a<len(ks) else a for a in ac]
    rows.append({"signature":s,"level":level,"instruction_ordinal":ordinal,
      "instruction_name":c["instruction_name"],"accounts":ac,"transaction":tx,
      "execution_authority":False})
  if len(rows)>=4:break
  if n and n%10==0:time.sleep(.3)
 return {"revision":"USLS_061","signature_count":len(sigs),"hydrated_count":hydrated,
  "exact_trade_count":len(rows),"rows":rows,"rpc_url_redacted":"configured" if os.environ.get("SOLANA_RPC_URL") else "public_fallback",
  "execution_authority":False,"read_only":True}

def write(root):
 d=build(root);p=Path(root)/"runtime_state/solana_opportunities/universal_trade_tape/launchlab_deep_trade_census.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
