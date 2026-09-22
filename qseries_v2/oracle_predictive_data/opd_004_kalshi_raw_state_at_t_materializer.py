
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter
import hashlib, json

from qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect

PAGE_SIZE = 50000
MAX_PAGES = 6
SOURCE = "source.kalshi.market_data"

def _hash(x):
    return hashlib.sha256(
        json.dumps(x, sort_keys=True, separators=(",", ":"), default=str).encode()
    ).hexdigest()

def _epoch(msg, outer):
    if msg.get("ts") is not None:
        try: return float(msg["ts"]), "payload.message.ts"
        except Exception: pass
    if msg.get("ts_ms") is not None:
        try: return float(msg["ts_ms"])/1000.0, "payload.message.ts_ms"
        except Exception: pass
    if msg.get("time"):
        try:
            d=datetime.fromisoformat(str(msg["time"]).replace("Z","+00:00"))
            if d.tzinfo is None: d=d.replace(tzinfo=timezone.utc)
            return d.timestamp(), "payload.message.time"
        except Exception: pass
    return outer.timestamp(), "outer_observed_at"

def _num(msg, *keys):
    for k in keys:
        if msg.get(k) is not None:
            try: return float(msg[k]), k
            except Exception: pass
    return None, None

def materialize(root=None):
    root=Path(root or Path.cwd())
    rows=[]
    cursor=None
    for _ in range(MAX_PAGES):
        with connect(root,autocommit=False) as c:
            with c.cursor() as q:
                q.execute("SET TRANSACTION READ ONLY")
                q.execute("SET LOCAL statement_timeout='20000ms'")
                sql=(
                    "SELECT sequence_number, observed_at, observation_type, canonical_observation_json "
                    "FROM public.oracle_canonical_observations WHERE source_id=%s"
                )
                args=[SOURCE]
                if cursor is not None:
                    sql+=" AND sequence_number < %s"; args.append(cursor)
                sql+=" ORDER BY sequence_number DESC LIMIT %s"; args.append(PAGE_SIZE)
                q.execute(sql,tuple(args)); batch=q.fetchall() or []
            c.rollback()
        if not batch: break
        cursor=min(int(x[0]) for x in batch)
        for seq,outer,typ,obj in batch:
            if not isinstance(obj,dict): continue
            payload=obj.get("payload")
            if not isinstance(payload,dict): continue
            msg=payload.get("message")
            if not isinstance(msg,dict): continue
            ticker=str(msg.get("market_ticker") or payload.get("source_market_id") or "")
            if not ticker.startswith("KX"): continue
            event_epoch,event_time_path=_epoch(msg,outer)
            trade_px,trade_px_field=_num(msg,"yes_price_dollars","price_dollars","last_price_dollars")
            yes_bid,_=_num(msg,"yes_bid_dollars")
            yes_ask,_=_num(msg,"yes_ask_dollars")
            yes_bid_size,_=_num(msg,"yes_bid_size_fp","yes_bid_size")
            yes_ask_size,_=_num(msg,"yes_ask_size_fp","yes_ask_size")
            last_trade_size,_=_num(msg,"last_trade_size_fp","last_trade_size")
            volume,_=_num(msg,"volume_fp","volume")
            oi,_=_num(msg,"open_interest_fp","open_interest")
            state={
                "sequence_number":int(seq),
                "ticker":ticker,
                "observation_type":str(typ),
                "event_epoch":event_epoch,
                "event_time_utc":datetime.fromtimestamp(event_epoch,timezone.utc).isoformat(),
                "event_time_path":event_time_path,
                "stored_observed_at":outer.isoformat(),
                "trade_price":trade_px,
                "trade_price_field":trade_px_field,
                "yes_bid":yes_bid,
                "yes_ask":yes_ask,
                "spread":(yes_ask-yes_bid if yes_bid is not None and yes_ask is not None else None),
                "yes_bid_size":yes_bid_size,
                "yes_ask_size":yes_ask_size,
                "last_trade_size":last_trade_size,
                "volume":volume,
                "open_interest":oi,
                "raw_message_fields":sorted(msg.keys()),
                "feature_side_only":True,
            }
            rows.append(state)

    rows.sort(key=lambda x:(x["event_epoch"],x["sequence_number"]))
    payload={
        "schema_version":"OPD-004",
        "rows":rows,
        "row_count":len(rows),
        "ticker_count":len(set(x["ticker"] for x in rows)),
        "event_time_paths":dict(Counter(x["event_time_path"] for x in rows)),
        "observation_types":dict(Counter(x["observation_type"] for x in rows)),
        "state_hash":_hash(rows),
        "feature_time_rule":"EVERY_ROW_REPRESENTS_ONLY_INFORMATION_AVAILABLE_AT_ITS_SOURCE_EVENT_TIME",
        "derived_prediction_features_created":False,
        "probability_enabled":False,
        "direction_enabled":False,
        "publication_allowed":False,
        "execution_authority":False,
    }
    p=root/"runtime"/"predictive_data"/"opd_004_kalshi_raw_state_at_t.json"
    p.write_text(json.dumps(payload,sort_keys=True,indent=2),encoding="utf-8")
    return payload,p
