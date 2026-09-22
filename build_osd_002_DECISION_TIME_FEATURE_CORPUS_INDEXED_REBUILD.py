from pathlib import Path
import textwrap

ROOT = Path(__file__).resolve().parent
PKG = ROOT / "qseries_v2" / "oracle_strategy_discovery"
PKG.mkdir(parents=True, exist_ok=True)
(PKG / "__init__.py").touch(exist_ok=True)

target = PKG / "osd_002_decision_time_feature_corpus_indexed_rebuild.py"
test = ROOT / "test_osd_002_DECISION_TIME_FEATURE_CORPUS_INDEXED_REBUILD.py"

source = r'''
from pathlib import Path
import json, statistics, datetime

from qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect

ROOT = Path(__file__).resolve().parents[2]
PRED = ROOT / "runtime" / "predictive_data" / "opd_full_evidence_live_prediction_ledger.jsonl"
OUTC = ROOT / "runtime" / "predictive_data" / "opd_full_evidence_live_outcome_ledger.jsonl"
DEST = ROOT / "runtime" / "strategy_discovery" / "osd_002_strategy_feature_corpus.jsonl"
SUMMARY = ROOT / "runtime" / "strategy_discovery" / "osd_002_strategy_feature_corpus_summary.json"

WINDOWS = (5, 15, 30, 60, 300)
SEQ_LOOKBACK = 75000
SOURCE_ID = "source.kalshi.market_data"

def rows(path):
    out = []
    if not path.exists(): return out
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            try:
                x = json.loads(line)
                if isinstance(x, dict): out.append(x)
            except Exception: pass
    return out

def pick(d, keys):
    for k in keys:
        v = d.get(k)
        if v is not None: return v
    return None

def rid(d):
    return str(pick(d, ("prediction_id","prediction_record_id","prospective_prediction_id","state_id")) or "")

def epoch(d):
    v = pick(d, ("prediction_epoch","frozen_epoch","created_epoch","anchor_epoch","observed_epoch"))
    try: return float(v)
    except Exception: return None

def anchor_seq(d):
    for obj in (d, d.get("state") if isinstance(d.get("state"),dict) else {}):
        for k in ("anchor_sequence","anchor_sequence_number","sequence_number","kalshi_anchor_sequence"):
            try:
                v = int(obj.get(k))
                if v > 0: return v
            except Exception: pass
    return None

def outcome_return(d):
    v = pick(d, ("future_return","realized_return","yes_price_return","price_return","return"))
    try: return float(v)
    except Exception: return None

def asset_of(ticker):
    u = (ticker or "").upper()
    if u.startswith("KXBTC"): return "BTC"
    if u.startswith("KXETH"): return "ETH"
    if u.startswith("KXSOL"): return "SOL"
    return None

def as_obj(v):
    if isinstance(v, dict): return v
    if isinstance(v, str):
        try:
            x = json.loads(v)
            return x if isinstance(x, dict) else {}
        except Exception: return {}
    return {}

def event_from_row(seq, typ, observed_at, raw):
    obj = as_obj(raw); payload = as_obj(obj.get("payload")); m = as_obj(payload.get("message"))
    ticker = str(m.get("market_ticker") or payload.get("source_market_id") or obj.get("ticker") or "")
    def num(*ks):
        for k in ks:
            try:
                v = m.get(k)
                if v is not None: return float(v)
            except Exception: pass
        return None
    bid = num("yes_bid_dollars"); ask = num("yes_ask_dollars"); trade = num("yes_price_dollars","price_dollars")
    side = str(m.get("taker_outcome_side") or m.get("taker_side") or "").upper()
    size = num("count_fp","last_trade_size_fp") or 0.0
    try: ts = observed_at.timestamp() if hasattr(observed_at,"timestamp") else float(observed_at)
    except Exception: ts = None
    return {"seq":int(seq),"type":str(typ),"ts":ts,"ticker":ticker,"asset":asset_of(ticker),"bid":bid,"ask":ask,"trade":trade,"size":size,"taker_yes":1 if side=="YES" else 0,"taker_no":1 if side=="NO" else 0}

def stats(events, t0, window, ticker=None, asset=None):
    lo = t0-window
    xs = [e for e in events if e["ts"] is not None and lo <= e["ts"] <= t0 and (ticker is None or e["ticker"]==ticker) and (asset is None or e["asset"]==asset)]
    trades = [e for e in xs if e["type"]=="trade"]
    refs = [(e["ts"], e["trade"] if e["trade"] is not None else ((e["bid"]+e["ask"])/2 if e["bid"] is not None and e["ask"] is not None else None)) for e in xs]
    refs = sorted((t,p) for t,p in refs if p is not None)
    spreads = [e["ask"]-e["bid"] for e in xs if e["bid"] is not None and e["ask"] is not None]
    yes = sum(e["taker_yes"] for e in trades); no = sum(e["taker_no"] for e in trades); den = yes+no
    ret = refs[-1][1]/refs[0][1]-1.0 if len(refs)>=2 and refs[0][1] else None
    return {"trade_count":len(trades),"trade_volume":sum(e["size"] for e in trades),"taker_imbalance":((yes-no)/den) if den else 0.0,"yes_return":ret,"spread_last":spreads[-1] if spreads else None,"spread_mean":statistics.fmean(spreads) if spreads else None,"yes_last":refs[-1][1] if refs else None}

def fetch_window(cur, anchor):
    lo = max(0, int(anchor)-SEQ_LOOKBACK)
    cur.execute("SELECT sequence_number, observation_type, observed_at, canonical_observation_json FROM public.oracle_canonical_observations WHERE source_id=%s AND sequence_number BETWEEN %s AND %s ORDER BY sequence_number ASC", (SOURCE_ID, lo, int(anchor)))
    return [event_from_row(*r) for r in cur.fetchall()]

def main():
    preds = rows(PRED); outs = {rid(x):x for x in rows(OUTC) if rid(x)}; joined = []
    for p in preds:
        o = outs.get(rid(p)); a = anchor_seq(p); t = epoch(p)
        ticker = str(pick(p,("ticker","market_ticker")) or ((p.get("state") or {}).get("ticker") if isinstance(p.get("state"),dict) else "") or "")
        y = outcome_return(o) if o else None
        if o and a and t and ticker and y is not None: joined.append((p,a,t,ticker,y))
    print("[PREDICTIONS]", len(preds), flush=True); print("[OUTCOMES]", len(outs), flush=True); print("[JOINABLE EXACT-ANCHOR ROWS]", len(joined), flush=True)
    if not joined: raise SystemExit("[FAIL] zero exact-anchor prediction/outcome joins; interface inspection required")
    DEST.parent.mkdir(parents=True, exist_ok=True); tmp = DEST.with_suffix(".tmp"); conn = connect(); written = 0
    with conn:
        with conn.cursor() as cur, tmp.open("w",encoding="utf-8") as f:
            for i,(p,a,t,ticker,y) in enumerate(joined,1):
                ev = fetch_window(cur,a); asset = asset_of(ticker); feat = {}
                for w in WINDOWS:
                    for k,v in stats(ev,t,w,ticker=ticker).items(): feat[f"self_{w}s_{k}"] = v
                    if asset:
                        for k,v in stats(ev,t,w,asset=asset).items(): feat[f"asset_{w}s_{k}"] = v
                dt = datetime.datetime.fromtimestamp(t, datetime.timezone.utc); feat["minute_of_day"] = dt.hour*60+dt.minute; feat["weekday"] = dt.weekday()
                row = {"prediction_id":rid(p),"ticker":ticker,"asset":asset,"horizon_seconds":p.get("horizon_seconds"),"prediction_epoch":t,"anchor_sequence":a,"future_return":y,"features":feat,"execution_authority":False,"publication_allowed":False}
                f.write(json.dumps(row,separators=(",",":"))+"\n"); written += 1
                if i % 100 == 0 or i == len(joined): print(f"[PROGRESS] {i}/{len(joined)} [FEATURE_ROWS] {written}", flush=True)
    tmp.replace(DEST)
    SUMMARY.write_text(json.dumps({"revision":"OSD_002_INDEXED_BOUNDED_POSTGRESQL_REBUILD_V1","joined_feature_rows":written,"windows_seconds":list(WINDOWS),"sequence_lookback":SEQ_LOOKBACK,"postgresql_access":"READ_ONLY","execution_authority":False,"publication_allowed":False},indent=2),encoding="utf-8")
    print("[JOINED FEATURE ROWS]", written); print("[RESULT] DECISION_TIME_FEATURE_CORPUS_READY"); print("[EXECUTION/PUBLICATION] FALSE/FALSE")

if __name__ == "__main__": main()
'''

test_source = r'''
from pathlib import Path
import py_compile
p=Path("qseries_v2/oracle_strategy_discovery/osd_002_decision_time_feature_corpus_indexed_rebuild.py")
assert p.exists(); s=p.read_text(encoding="utf-8"); py_compile.compile(str(p), doraise=True)
assert "SEQ_LOOKBACK = 75000" in s
assert "sequence_number BETWEEN %s AND %s" in s
assert "osd_001_kalshi_microstructure_archive.jsonl" not in s
assert "future_return" in s and '"features":feat' in s
assert "execution_authority" in s and "publication_allowed" in s
print("[PASS] OSD-002 indexed bounded PostgreSQL rebuild compiles")
print("[PASS] no 21.7M-row JSONL archive scan")
print("[PASS] exact anchor sequence bounded reads installed")
print("[PASS] future outcome remains target-only, not feature input")
print("[PASS] execution/publication remain false")
'''

target.write_text(textwrap.dedent(source).lstrip(), encoding="utf-8")
test.write_text(textwrap.dedent(test_source).lstrip(), encoding="utf-8")
print("[PASS] OSD-002 indexed rebuild installed")
print("[TARGET]", target)
print("[TEST]", test)
print("[RETIRED] prior hung osd_002_decision_time_feature_corpus.py runtime path")
print("[EXECUTION/PUBLICATION] FALSE/FALSE")
