from __future__ import annotations
import json,statistics
from collections import Counter,defaultdict
from pathlib import Path

H=(5,15,30)

def _window(rows,h):
 r=[x for x in rows if x["birth_age_seconds"]<=h]
 traders=[x["trader"] for x in r if x.get("trader")]
 abs_base=[x["base_amount"] for x in r if x.get("base_amount")]
 by=defaultdict(float)
 for x in r:
  if x.get("trader") and x.get("base_amount"):by[x["trader"]]+=x["base_amount"]
 total=sum(abs_base)
 return {"horizon_seconds":h,"trade_count":len(r),
  "buy_count":sum(1 for x in r if x["side"]=="BUY"),
  "sell_count":sum(1 for x in r if x["side"]=="SELL"),
  "unique_trader_count":len(set(traders)),
  "repeat_trader_count":sum(1 for _,n in Counter(traders).items() if n>1),
  "resolved_base_volume":total,
  "signed_base_flow":sum((x["base_amount"] if x["side"]=="BUY" else -x["base_amount"])
                         for x in r if x.get("base_amount")),
  "largest_trader_base_share":(max(by.values())/total if by and total>0 else None)}

def build(root):
 root=Path(root);base=root/"runtime_state/solana_opportunities/universal_trade_tape"
 d=json.loads((base/"pump_enriched_trade_tape.json").read_text(encoding="utf-8"))
 rows=sorted(d["rows"],key=lambda x:x["observed_unix"])
 gaps=[rows[i]["observed_unix"]-rows[i-1]["observed_unix"] for i in range(1,len(rows))]
 duration=max(0.0,rows[-1]["observed_unix"]-rows[0]["observed_unix"]) if len(rows)>1 else 0.0
 windows=[_window(rows,h) for h in H]
 return {"revision":"USLS_039","trade_count":len(rows),
  "buy_count":sum(1 for x in rows if x["side"]=="BUY"),
  "sell_count":sum(1 for x in rows if x["side"]=="SELL"),
  "unique_trader_count":len({x["trader"] for x in rows if x.get("trader")}),
  "median_intertrade_seconds":statistics.median(gaps) if gaps else None,
  "trades_per_second":len(rows)/duration if duration>0 else None,
  "windows":windows,"quote_flow_available":any(x.get("quote_amount") is not None for x in rows),
  "profitability_claimed":False,"execution_authority":False,"read_only":True}

def write(root):
 d=build(root);p=Path(root)/"runtime_state/solana_opportunities/universal_trade_tape/pump_early_trade_flow_features.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
