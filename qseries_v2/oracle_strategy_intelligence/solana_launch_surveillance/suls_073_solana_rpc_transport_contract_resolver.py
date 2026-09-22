from __future__ import annotations
import inspect,json,os,re
import qseries_v2.oracle_adapters.independent.oad_148_solana_mainnet_chain_state_acquisition as o148

ENV_KEYS=("SOLANA_RPC_URL","SOLANA_MAINNET_RPC_URL","RPC_URL")
def resolve():
 src=inspect.getsource(o148)
 candidates=[]
 for k in ENV_KEYS:
  v=os.environ.get(k)
  if v and v.startswith(("http://","https://")):candidates.append({"source":"env:"+k,"url":v})
 for m in re.finditer(r'https?://[^"\'\s)]+',src):
  candidates.append({"source":"oad_148_source","url":m.group(0)})
 for k,v in vars(o148).items():
  if isinstance(v,str) and v.startswith(("http://","https://")):
   candidates.append({"source":"oad_148_global:"+k,"url":v})
 ded=[];seen=set()
 for x in candidates:
  if x["url"] not in seen:seen.add(x["url"]);ded.append(x)
 selected=ded[0]["url"] if ded else None
 ws=None
 if selected:
  ws=("wss://"+selected[8:]) if selected.startswith("https://") else ("ws://"+selected[7:])
 return {"revision":"SULS_073","http_candidates":ded,"selected_http":selected,"derived_ws":ws,
  "rpc_source_excerpt":"\n".join(x for x in src.splitlines() if "url" in x.lower() or "rpc" in x.lower())[:12000],
  "execution_authority":False,"read_only":True}

def write(root):
 d=resolve();p=root/"runtime_state/solana_opportunities/launch_surveillance/solana_rpc_transport_contract.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
