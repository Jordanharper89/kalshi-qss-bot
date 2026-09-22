from collections import defaultdict, Counter
from bisect import bisect_right
import json, re, math, statistics
from pathlib import Path
from qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect

ROOT = Path.cwd()
TICKER_RE = re.compile(r"\bKXBTC15M-[A-Z0-9-]+\b", re.I)
RAW_SPOT = "source.crypto.condition.btc.coinbase.spot_price"
KALSHI_SOURCE = "source.kalshi.market_data"
PRICE_KEYS = ("yes_price_dollars","price_dollars","last_price_dollars","yes_bid_dollars","yes_ask_dollars")

def walk(x):
    if isinstance(x, dict):
        for k, v in x.items():
            yield str(k), v
            yield from walk(v)
    elif isinstance(x, list):
        for v in x:
            yield from walk(v)

def asdict(obj):
    try:
        return obj if isinstance(obj, dict) else json.loads(obj)
    except Exception:
        return {}

def numeric_map(obj):
    d = asdict(obj)
    out = {}
    for k, v in walk(d):
        try:
            f = float(v)
            if math.isfinite(f):
                out.setdefault(k.lower(), f)
        except Exception:
            pass
    return out

def scalar_value(obj, preferred=()):
    vals = numeric_map(obj)
    for k in preferred:
        if k in vals:
            return vals[k]
    uniq = list(vals.values())
    return uniq[0] if len(uniq) == 1 else None

def kalshi_parse(obj):
    d = asdict(obj)
    text = json.dumps(d, default=str).upper()
    m = TICKER_RE.search(text)
    if not m:
        return None, None
    vals = numeric_map(d)
    p = None
    for k in PRICE_KEYS[:3]:
        v = vals.get(k)
        if v is not None and 0 <= v <= 1:
            p = v
            break
    bid = vals.get("yes_bid_dollars")
    ask = vals.get("yes_ask_dollars")
    if p is None and bid is not None and ask is not None and 0 <= bid <= ask <= 1:
        p = (bid + ask) / 2
    return m.group(0), p

def load_rows():
    rows = []
    cursor = None
    for page in range(1, 5):
        with connect(ROOT, autocommit=False) as c:
            with c.cursor() as q:
                q.execute("SET TRANSACTION READ ONLY")
                q.execute("SET LOCAL statement_timeout='15000ms'")
                sql = """SELECT sequence_number, observed_at, source_id, canonical_observation_json
                         FROM public.oracle_canonical_observations"""
                args = []
                if cursor is not None:
                    sql += " WHERE sequence_number < %s"
                    args.append(cursor)
                sql += " ORDER BY sequence_number DESC LIMIT 50000"
                q.execute(sql, tuple(args))
                batch = q.fetchall() or []
            c.rollback()
        print("[PAGE]", page, "rows=", len(batch))
        if not batch:
            break
        rows += batch
        cursor = min(int(x[0]) for x in batch)
    return rows

def build_series(rows):
    spot = []
    kalshi = defaultdict(list)
    for seq, ts, source, obj in rows:
        if ts is None:
            continue
        s = str(source)
        if s == RAW_SPOT:
            v = scalar_value(obj, ("spot_price","price","value"))
            if v is not None and v > 0:
                spot.append((ts, int(seq), float(v)))
        elif s == KALSHI_SOURCE:
            ticker, p = kalshi_parse(obj)
            if ticker and p is not None:
                kalshi[ticker].append((ts, int(seq), float(p)))
    spot.sort(key=lambda x:(x[0],x[1]))
    for t in kalshi:
        kalshi[t].sort(key=lambda x:(x[0],x[1]))
    return spot, kalshi

def rolling_returns(spot, lookback_seconds=60):
    out = []
    times = [x[0] for x in spot]
    for i, (ts, seq, px) in enumerate(spot):
        j = bisect_right(times, ts) - 1
        k = j
        while k > 0 and (ts - spot[k][0]).total_seconds() < lookback_seconds:
            k -= 1
        if k >= 0 and spot[k][2] > 0 and spot[k][0] < ts:
            ret = (px / spot[k][2]) - 1.0
            out.append((ts, seq, px, ret, (ts-spot[k][0]).total_seconds()))
    return out

def empirical_threshold(vals, q=0.95):
    if not vals:
        return None
    a = sorted(vals)
    idx = min(len(a)-1, max(0, int(round((len(a)-1)*q))))
    return a[idx]

def detect_shocks(spot):
    rr = rolling_returns(spot, 60)
    mags = [abs(x[3]) for x in rr]
    thr = empirical_threshold(mags, 0.95)
    if thr is None:
        return [], None
    shocks = []
    last_ts = None
    for row in rr:
        ts, seq, px, ret, span = row
        if abs(ret) < thr:
            continue
        if last_ts is not None and (ts-last_ts).total_seconds() < 30:
            continue
        shocks.append({"ts":ts,"seq":seq,"spot":px,"ret60":ret,"span":span,"threshold":thr})
        last_ts = ts
    return shocks, thr

def choose_contract(kalshi, ts):
    candidates = []
    for t, pts in kalshi.items():
        times = [x[0] for x in pts]
        i = bisect_right(times, ts) - 1
        if i < 0:
            continue
        lag = (ts - pts[i][0]).total_seconds()
        if 0 <= lag <= 90:
            candidates.append((lag, t, i, pts))
    if not candidates:
        return None
    candidates.sort(key=lambda x:x[0])
    return candidates[0]

def reaction_curve(shock, kalshi):
    chosen = choose_contract(kalshi, shock["ts"])
    if chosen is None:
        return None
    lag0, ticker, i0, pts = chosen
    ts0, seq0, p0 = pts[i0]
    horizons = (5,15,30,60,120,300)
    out = {"ticker":ticker,"shock_ts":shock["ts"],"shock_ret60":shock["ret60"],
           "base_ts":ts0,"base_price":p0,"base_lag_s":lag0}
    future = [x for x in pts[i0+1:] if 0 < (x[0]-shock["ts"]).total_seconds() <= 300]
    if not future:
        return None
    prices = [x[2] for x in future]
    out["mfe"] = max(p-p0 for p in prices)
    out["mae"] = max(p0-p for p in prices)
    peak = max(future, key=lambda x:x[2])
    trough = min(future, key=lambda x:x[2])
    out["time_to_peak_s"] = (peak[0]-shock["ts"]).total_seconds()
    out["time_to_trough_s"] = (trough[0]-shock["ts"]).total_seconds()
    for h in horizons:
        f = [x for x in future if (x[0]-shock["ts"]).total_seconds() <= h]
        if f:
            out[f"d{h}"] = f[-1][2]-p0
    return out

def first_material_reaction(curve, threshold=0.03):
    for h in (5,15,30,60,120,300):
        d = curve.get(f"d{h}")
        if d is not None and abs(d) >= threshold:
            return h
    return None

def classify_curve(curve):
    first = first_material_reaction(curve, 0.03)
    mfe, mae = curve.get("mfe",0.0), curve.get("mae",0.0)
    d300 = curve.get("d300")
    direction = 1 if curve["shock_ret60"] >= 0 else -1
    signed_mfe = mfe if direction > 0 else mae
    signed_adverse = mae if direction > 0 else mfe
    if first is not None and first <= 15:
        regime = "FAST_REACTION"
    elif first is not None and first <= 60:
        regime = "DELAYED_REACTION"
    elif signed_mfe >= 0.05 and first is None:
        regime = "UNDERREACTION"
    else:
        regime = "NO_CLEAR_REACTION"
    if signed_mfe >= 0.05 and signed_adverse >= 0.03:
        regime = "OVERSHOOT_REVERSAL"
    return regime

rows = load_rows()
spot, kalshi = build_series(rows)
shocks, thr = detect_shocks(spot)
curves = []
for s in shocks:
    c = reaction_curve(s, kalshi)
    if c:
        curves.append(c)
print("[SHOCKS]", len(shocks))
print("[REACTION_CURVES]", len(curves))
for c in curves[:40]:
    print("[CURVE]", c["shock_ts"], c["ticker"],
          "shock_ret60=", round(c["shock_ret60"],8),
          "base_price=", round(c["base_price"],4),
          "base_lag_s=", round(c["base_lag_s"],3),
          "d5=", c.get("d5"), "d15=", c.get("d15"), "d30=", c.get("d30"),
          "d60=", c.get("d60"), "d120=", c.get("d120"), "d300=", c.get("d300"),
          "mfe=", round(c["mfe"],4), "mae=", round(c["mae"],4),
          "time_to_peak_s=", round(c["time_to_peak_s"],3))
print("[PASS] OPA-032 Kalshi reaction-curve reconstruction audit complete")
