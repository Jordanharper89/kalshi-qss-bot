from __future__ import annotations
import json,statistics
from collections import Counter,defaultdict
from pathlib import Path
H=(5,15,30)

def window(rows,h):
 r=[x for x in rows if x["birth_age_seconds"]<=h and x["decoder_state"]=="TRADE_EVENT_ECONOMICS_EXACT"]
 users=[x["trader"] for x in r if x.get("trader")];q=[x["quote_amount"] for x in r if x.get("quote_amount") is not None]
 by=defaultdict(float)
 for x in r:
  if x.get("trader") and x.get("quote_amount") is not None:by[x["trader"]]+=x["quote_amount"]
 total=sum(q)
 return {"horizon_seconds":h,"exact_trade_count":len(r),"buy_count":sum(x["side"]=="BUY" for x in r),
  "sell_count":sum(x["side"]=="SELL" for x in r),"unique_trader_count":len(set(users)),
  "repeat_trader_count":sum(n>1 for n in Counter(users).values()),
  "quote_volume_sol":total,
  "net_quote_flow_sol":sum((1 if x["side"]=="BUY" else -1)*x["quote_amount"] for x in r),
  "largest_trader_quote_share":max(by.values())/total if by and total else None}

def build(root):
 base=Path(root)/"runtime_state/solana_opportunities/universal_trade_tape"
 d=json.loads((base/"pump_exact_economic_trade_tape.json").read_text(encoding="utf-8"))
 rows=sorted(d["rows"],key=lambda x:x["observed_unix"])
 exact=[x for x in rows if x["decoder_state"]=="TRADE_EVENT_ECONOMICS_EXACT"]
 gaps=[exact[i]["observed_unix"]-exact[i-1]["observed_unix"] for i in range(1,len(exact))]
 return {"revision":"USLS_043","captured_trade_count":len(rows),"economic_exact_count":len(exact),
  "coverage_ratio":len(exact)/len(rows) if rows else 0.0,
  "median_intertrade_seconds":statistics.median(gaps) if gaps else None,
  "windows":[window(rows,h) for h in H],"profitability_claimed":False,
  "execution_authority":False,"read_only":True}

def write(root):
 d=build(root);p=Path(root)/"runtime_state/solana_opportunities/universal_trade_tape/pump_exact_flow_features.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
