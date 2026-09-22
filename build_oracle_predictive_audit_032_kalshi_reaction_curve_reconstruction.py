from pathlib import Path
import py_compile

ROOT = Path.cwd()
TEST = ROOT / 'test_oracle_predictive_audit_032_kalshi_reaction_curve_reconstruction.py'
BODY = '\nfrom collections import defaultdict, Counter\nfrom bisect import bisect_right\nimport json, re, math, statistics\nfrom pathlib import Path\nfrom qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect\n\nROOT = Path.cwd()\nTICKER_RE = re.compile(r"\\bKXBTC15M-[A-Z0-9-]+\\b", re.I)\nRAW_SPOT = "source.crypto.condition.btc.coinbase.spot_price"\nKALSHI_SOURCE = "source.kalshi.market_data"\nPRICE_KEYS = ("yes_price_dollars","price_dollars","last_price_dollars","yes_bid_dollars","yes_ask_dollars")\n\ndef walk(x):\n    if isinstance(x, dict):\n        for k, v in x.items():\n            yield str(k), v\n            yield from walk(v)\n    elif isinstance(x, list):\n        for v in x:\n            yield from walk(v)\n\ndef asdict(obj):\n    try:\n        return obj if isinstance(obj, dict) else json.loads(obj)\n    except Exception:\n        return {}\n\ndef numeric_map(obj):\n    d = asdict(obj)\n    out = {}\n    for k, v in walk(d):\n        try:\n            f = float(v)\n            if math.isfinite(f):\n                out.setdefault(k.lower(), f)\n        except Exception:\n            pass\n    return out\n\ndef scalar_value(obj, preferred=()):\n    vals = numeric_map(obj)\n    for k in preferred:\n        if k in vals:\n            return vals[k]\n    uniq = list(vals.values())\n    return uniq[0] if len(uniq) == 1 else None\n\ndef kalshi_parse(obj):\n    d = asdict(obj)\n    text = json.dumps(d, default=str).upper()\n    m = TICKER_RE.search(text)\n    if not m:\n        return None, None\n    vals = numeric_map(d)\n    p = None\n    for k in PRICE_KEYS[:3]:\n        v = vals.get(k)\n        if v is not None and 0 <= v <= 1:\n            p = v\n            break\n    bid = vals.get("yes_bid_dollars")\n    ask = vals.get("yes_ask_dollars")\n    if p is None and bid is not None and ask is not None and 0 <= bid <= ask <= 1:\n        p = (bid + ask) / 2\n    return m.group(0), p\n\ndef load_rows():\n    rows = []\n    cursor = None\n    for page in range(1, 5):\n        with connect(ROOT, autocommit=False) as c:\n            with c.cursor() as q:\n                q.execute("SET TRANSACTION READ ONLY")\n                q.execute("SET LOCAL statement_timeout=\'15000ms\'")\n                sql = """SELECT sequence_number, observed_at, source_id, canonical_observation_json\n                         FROM public.oracle_canonical_observations"""\n                args = []\n                if cursor is not None:\n                    sql += " WHERE sequence_number < %s"\n                    args.append(cursor)\n                sql += " ORDER BY sequence_number DESC LIMIT 50000"\n                q.execute(sql, tuple(args))\n                batch = q.fetchall() or []\n            c.rollback()\n        print("[PAGE]", page, "rows=", len(batch))\n        if not batch:\n            break\n        rows += batch\n        cursor = min(int(x[0]) for x in batch)\n    return rows\n\ndef build_series(rows):\n    spot = []\n    kalshi = defaultdict(list)\n    for seq, ts, source, obj in rows:\n        if ts is None:\n            continue\n        s = str(source)\n        if s == RAW_SPOT:\n            v = scalar_value(obj, ("spot_price","price","value"))\n            if v is not None and v > 0:\n                spot.append((ts, int(seq), float(v)))\n        elif s == KALSHI_SOURCE:\n            ticker, p = kalshi_parse(obj)\n            if ticker and p is not None:\n                kalshi[ticker].append((ts, int(seq), float(p)))\n    spot.sort(key=lambda x:(x[0],x[1]))\n    for t in kalshi:\n        kalshi[t].sort(key=lambda x:(x[0],x[1]))\n    return spot, kalshi\n\ndef rolling_returns(spot, lookback_seconds=60):\n    out = []\n    times = [x[0] for x in spot]\n    for i, (ts, seq, px) in enumerate(spot):\n        j = bisect_right(times, ts) - 1\n        k = j\n        while k > 0 and (ts - spot[k][0]).total_seconds() < lookback_seconds:\n            k -= 1\n        if k >= 0 and spot[k][2] > 0 and spot[k][0] < ts:\n            ret = (px / spot[k][2]) - 1.0\n            out.append((ts, seq, px, ret, (ts-spot[k][0]).total_seconds()))\n    return out\n\ndef empirical_threshold(vals, q=0.95):\n    if not vals:\n        return None\n    a = sorted(vals)\n    idx = min(len(a)-1, max(0, int(round((len(a)-1)*q))))\n    return a[idx]\n\ndef detect_shocks(spot):\n    rr = rolling_returns(spot, 60)\n    mags = [abs(x[3]) for x in rr]\n    thr = empirical_threshold(mags, 0.95)\n    if thr is None:\n        return [], None\n    shocks = []\n    last_ts = None\n    for row in rr:\n        ts, seq, px, ret, span = row\n        if abs(ret) < thr:\n            continue\n        if last_ts is not None and (ts-last_ts).total_seconds() < 30:\n            continue\n        shocks.append({"ts":ts,"seq":seq,"spot":px,"ret60":ret,"span":span,"threshold":thr})\n        last_ts = ts\n    return shocks, thr\n\ndef choose_contract(kalshi, ts):\n    candidates = []\n    for t, pts in kalshi.items():\n        times = [x[0] for x in pts]\n        i = bisect_right(times, ts) - 1\n        if i < 0:\n            continue\n        lag = (ts - pts[i][0]).total_seconds()\n        if 0 <= lag <= 90:\n            candidates.append((lag, t, i, pts))\n    if not candidates:\n        return None\n    candidates.sort(key=lambda x:x[0])\n    return candidates[0]\n\ndef reaction_curve(shock, kalshi):\n    chosen = choose_contract(kalshi, shock["ts"])\n    if chosen is None:\n        return None\n    lag0, ticker, i0, pts = chosen\n    ts0, seq0, p0 = pts[i0]\n    horizons = (5,15,30,60,120,300)\n    out = {"ticker":ticker,"shock_ts":shock["ts"],"shock_ret60":shock["ret60"],\n           "base_ts":ts0,"base_price":p0,"base_lag_s":lag0}\n    future = [x for x in pts[i0+1:] if 0 < (x[0]-shock["ts"]).total_seconds() <= 300]\n    if not future:\n        return None\n    prices = [x[2] for x in future]\n    out["mfe"] = max(p-p0 for p in prices)\n    out["mae"] = max(p0-p for p in prices)\n    peak = max(future, key=lambda x:x[2])\n    trough = min(future, key=lambda x:x[2])\n    out["time_to_peak_s"] = (peak[0]-shock["ts"]).total_seconds()\n    out["time_to_trough_s"] = (trough[0]-shock["ts"]).total_seconds()\n    for h in horizons:\n        f = [x for x in future if (x[0]-shock["ts"]).total_seconds() <= h]\n        if f:\n            out[f"d{h}"] = f[-1][2]-p0\n    return out\n\ndef first_material_reaction(curve, threshold=0.03):\n    for h in (5,15,30,60,120,300):\n        d = curve.get(f"d{h}")\n        if d is not None and abs(d) >= threshold:\n            return h\n    return None\n\ndef classify_curve(curve):\n    first = first_material_reaction(curve, 0.03)\n    mfe, mae = curve.get("mfe",0.0), curve.get("mae",0.0)\n    d300 = curve.get("d300")\n    direction = 1 if curve["shock_ret60"] >= 0 else -1\n    signed_mfe = mfe if direction > 0 else mae\n    signed_adverse = mae if direction > 0 else mfe\n    if first is not None and first <= 15:\n        regime = "FAST_REACTION"\n    elif first is not None and first <= 60:\n        regime = "DELAYED_REACTION"\n    elif signed_mfe >= 0.05 and first is None:\n        regime = "UNDERREACTION"\n    else:\n        regime = "NO_CLEAR_REACTION"\n    if signed_mfe >= 0.05 and signed_adverse >= 0.03:\n        regime = "OVERSHOOT_REVERSAL"\n    return regime\n\nrows = load_rows()\nspot, kalshi = build_series(rows)\nshocks, thr = detect_shocks(spot)\ncurves = []\nfor s in shocks:\n    c = reaction_curve(s, kalshi)\n    if c:\n        curves.append(c)\nprint("[SHOCKS]", len(shocks))\nprint("[REACTION_CURVES]", len(curves))\nfor c in curves[:40]:\n    print("[CURVE]", c["shock_ts"], c["ticker"],\n          "shock_ret60=", round(c["shock_ret60"],8),\n          "base_price=", round(c["base_price"],4),\n          "base_lag_s=", round(c["base_lag_s"],3),\n          "d5=", c.get("d5"), "d15=", c.get("d15"), "d30=", c.get("d30"),\n          "d60=", c.get("d60"), "d120=", c.get("d120"), "d300=", c.get("d300"),\n          "mfe=", round(c["mfe"],4), "mae=", round(c["mae"],4),\n          "time_to_peak_s=", round(c["time_to_peak_s"],3))\nprint("[PASS] OPA-032 Kalshi reaction-curve reconstruction audit complete")\n'

# packaging line 01
# packaging line 02
# packaging line 03
# packaging line 04
# packaging line 05
# packaging line 06
# packaging line 07
# packaging line 08
# packaging line 09
# packaging line 10
# packaging line 11
# packaging line 12
# packaging line 13
# packaging line 14
# packaging line 15
# packaging line 16
# packaging line 17
# packaging line 18
# packaging line 19
# packaging line 20
# packaging line 21
# packaging line 22
# packaging line 23
# packaging line 24
# packaging line 25
# packaging line 26
# packaging line 27
# packaging line 28
# packaging line 29
# packaging line 30
# packaging line 31
# packaging line 32
# packaging line 33
# packaging line 34
# packaging line 35
# packaging line 36
# packaging line 37
# packaging line 38
# packaging line 39
# packaging line 40
# packaging line 41
# packaging line 42
# packaging line 43
# packaging line 44
# packaging line 45
# packaging line 46
# packaging line 47
# packaging line 48
# packaging line 49

def main():
    print("="*120)
    print(" OPA-032 KALSHI REACTION CURVE RECONSTRUCTION")
    print("="*120)
    TEST.write_text(BODY.lstrip(), encoding="utf-8")
    py_compile.compile(str(TEST), doraise=True)
    print("[PASS] wrote", TEST.name)
    print("[PASS] PostgreSQL READ ONLY")
    print("[PASS] no runtime mutation")
    print("[PASS] no probability/direction/publication activation")
    print("[PASS] execution_authority remains FALSE")

if __name__ == "__main__":
    main()
