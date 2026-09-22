import json
from pathlib import Path
from datetime import datetime,timezone
from .chf_001_foundation import runtime_dir

REVISION="CHF-003"

def _f(v):
    try:return float(v)
    except Exception:return None

def normalize_message(envelope):
    msg=envelope.get("message") or {}
    received_at=envelope.get("received_at")
    channel=msg.get("channel")
    ts=msg.get("timestamp") or received_at
    out=[]
    for ev in msg.get("events") or []:
        et=ev.get("type")
        if channel=="market_trades":
            for tr in ev.get("trades") or []:
                out.append({"observed_at":tr.get("time") or ts,"received_at":received_at,
                    "source_id":"source.crypto.hf.coinbase.market_trade","observation_type":"coinbase_market_trade",
                    "product_id":tr.get("product_id"),"price":_f(tr.get("price")),"size":_f(tr.get("size")),
                    "maker_side":tr.get("side"),"trade_id":tr.get("trade_id"),"channel":channel})
        elif channel=="ticker":
            ticks=ev.get("tickers") or []
            for t in ticks:
                out.append({"observed_at":ts,"received_at":received_at,
                    "source_id":"source.crypto.hf.coinbase.ticker","observation_type":"coinbase_ticker",
                    "product_id":t.get("product_id"),"price":_f(t.get("price")),
                    "best_bid":_f(t.get("best_bid")),"best_ask":_f(t.get("best_ask")),
                    "volume_24_h":_f(t.get("volume_24_h")),"channel":channel})
        elif channel=="level2":
            pid=ev.get("product_id")
            out.append({"observed_at":ts,"received_at":received_at,
                "source_id":"source.crypto.hf.coinbase.level2","observation_type":"coinbase_level2",
                "product_id":pid,"event_type":et,"updates":ev.get("updates") or [],"channel":channel})
        elif channel=="heartbeats":
            out.append({"observed_at":ts,"received_at":received_at,
                "source_id":"source.crypto.hf.coinbase.heartbeat","observation_type":"coinbase_heartbeat",
                "heartbeat_counter":ev.get("heartbeat_counter"),"channel":channel})
    return out

def normalize_journal(root:Path,start_offset=0):
    d=runtime_dir(Path(root)); raw=d/"raw_events.jsonl"; canon=d/"canonical_events.jsonl"; n=0
    if not raw.exists(): return 0
    with raw.open("r",encoding="utf-8") as src, canon.open("a",encoding="utf-8",buffering=1) as dst:
        src.seek(start_offset)
        for line in src:
            try: env=json.loads(line)
            except Exception: continue
            for item in normalize_message(env):
                dst.write(json.dumps(item,separators=(",",":"),default=str)+"\n"); n+=1
    return n
