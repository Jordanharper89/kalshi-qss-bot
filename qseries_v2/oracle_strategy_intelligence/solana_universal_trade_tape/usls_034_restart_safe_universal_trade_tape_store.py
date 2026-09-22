from __future__ import annotations
import json,time
from pathlib import Path

def merge(root):
 root=Path(root);base=root/"runtime_state/solana_opportunities/universal_trade_tape"
 src=json.loads((base/"pump_normalized_trade_tape.json").read_text(encoding="utf-8"))
 p=base/"universal_trade_tape.json"
 old=json.loads(p.read_text(encoding="utf-8")) if p.exists() else {"revision":"USLS_034","trades":{}}
 trades=old.get("trades") or {};before=len(trades)
 for x in src.get("rows") or []:trades.setdefault(x["trade_id"],x)
 old.update({"revision":"USLS_034","trades":trades,"trade_count":len(trades),
  "updated_unix":time.time(),"append_only":True,"execution_authority":False,"read_only":True})
 p.write_text(json.dumps(old,indent=2,sort_keys=True),encoding="utf-8")
 return p,old,before,len(trades)

def write(root):return merge(root)
