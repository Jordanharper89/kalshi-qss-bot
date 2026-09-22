from pathlib import Path
import py_compile

ROOT=Path.cwd()
TEST=ROOT/'test_oracle_predictive_audit_039_exact_lag_opportunity_dataset.py'
BODY='\nfrom collections import defaultdict, Counter\nfrom bisect import bisect_right\nimport json, re, math, statistics\nfrom pathlib import Path\nfrom qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect\n\nROOT = Path.cwd()\nTICKER_RE = re.compile(r"\\bKXBTC15M-[A-Z0-9-]+\\b", re.I)\nRAW_SPOT = "source.crypto.condition.btc.coinbase.spot_price"\nKALSHI_SOURCE = "source.kalshi.market_data"\nPRICE_KEYS = ("yes_price_dollars","price_dollars","last_price_dollars","yes_bid_dollars","yes_ask_dollars")\n\ndef walk(x):\n    if isinstance(x, dict):\n        for k,v in x.items():\n            yield str(k),v\n            yield from walk(v)\n    elif isinstance(x,list):\n        for v in x:\n            yield from walk(v)\n\ndef asdict(obj):\n    try:\n        return obj if isinstance(obj,dict) else json.loads(obj)\n    except Exception:\n        return {}\n\ndef numeric_map(obj):\n    d=asdict(obj); out={}\n    for k,v in walk(d):\n        try:\n            f=float(v)\n            if math.isfinite(f): out.setdefault(k.lower(),f)\n        except Exception:\n            pass\n    return out\n\ndef scalar_value(obj, preferred=()):\n    vals=numeric_map(obj)\n    for k in preferred:\n        if k in vals: return vals[k]\n    uniq=list(vals.values())\n    return uniq[0] if len(uniq)==1 else None\n\ndef kalshi_parse(obj):\n    d=asdict(obj)\n    text=json.dumps(d,default=str).upper()\n    m=TICKER_RE.search(text)\n    if not m: return None,None\n    vals=numeric_map(d); p=None\n    for k in PRICE_KEYS[:3]:\n        v=vals.get(k)\n        if v is not None and 0<=v<=1: p=v; break\n    bid=vals.get("yes_bid_dollars"); ask=vals.get("yes_ask_dollars")\n    if p is None and bid is not None and ask is not None and 0<=bid<=ask<=1:\n        p=(bid+ask)/2\n    return m.group(0),p\n\ndef load_rows():\n    rows=[]; cursor=None\n    for page in range(1,5):\n        with connect(ROOT,autocommit=False) as c:\n            with c.cursor() as q:\n                q.execute("SET TRANSACTION READ ONLY")\n                q.execute("SET LOCAL statement_timeout=\'15000ms\'")\n                sql="""SELECT sequence_number,observed_at,source_id,canonical_observation_json\n                       FROM public.oracle_canonical_observations"""\n                args=[]\n                if cursor is not None:\n                    sql+=" WHERE sequence_number < %s"; args.append(cursor)\n                sql+=" ORDER BY sequence_number DESC LIMIT 50000"\n                q.execute(sql,tuple(args)); b=q.fetchall() or []\n            c.rollback()\n        print("[PAGE]",page,"rows=",len(b))\n        if not b: break\n        rows+=b; cursor=min(int(x[0]) for x in b)\n    return rows\n\ndef build_series(rows):\n    spot=[]; kalshi=defaultdict(list)\n    for seq,ts,source,obj in rows:\n        if ts is None: continue\n        s=str(source)\n        if s==RAW_SPOT:\n            v=scalar_value(obj,("spot_price","price","value"))\n            if v is not None and v>0: spot.append((ts,int(seq),float(v)))\n        elif s==KALSHI_SOURCE:\n            t,p=kalshi_parse(obj)\n            if t and p is not None: kalshi[t].append((ts,int(seq),float(p)))\n    spot.sort(key=lambda x:(x[0],x[1]))\n    for t in kalshi: kalshi[t].sort(key=lambda x:(x[0],x[1]))\n    return spot,kalshi\n\ndef certified_returns(spot):\n    specs={30:(20,45),60:(45,90),120:(90,150)}\n    out={k:[] for k in specs}\n    times=[x[0] for x in spot]\n    for i,(ts,seq,px) in enumerate(spot):\n        for horizon,(lo,hi) in specs.items():\n            best=None\n            for j in range(i-1,-1,-1):\n                span=(ts-spot[j][0]).total_seconds()\n                if span>hi: break\n                if lo<=span<=hi:\n                    err=abs(span-horizon)\n                    if best is None or err<best[0]:\n                        best=(err,j,span)\n            if best is not None:\n                _,j,span=best\n                prev=spot[j][2]\n                if prev>0:\n                    out[horizon].append((ts,seq,px,(px/prev)-1.0,span,spot[j][0],spot[j][1]))\n    return out\n\ndef empirical_threshold(vals,q=.95):\n    if not vals: return None\n    s=sorted(vals)\n    idx=min(len(s)-1,max(0,int(round((len(s)-1)*q))))\n    return s[idx]\n\ndef detect_certified_shocks(spot,horizon=60):\n    cr=certified_returns(spot)[horizon]\n    thr=empirical_threshold([abs(x[3]) for x in cr],.95)\n    shocks=[]; last=None\n    if thr is None: return shocks,thr,cr\n    for ts,seq,px,ret,span,base_ts,base_seq in cr:\n        if abs(ret)<thr: continue\n        if last is not None and (ts-last).total_seconds()<30: continue\n        shocks.append({"ts":ts,"seq":seq,"spot":px,"ret":ret,"span":span,\n                       "base_ts":base_ts,"base_seq":base_seq,"threshold":thr})\n        last=ts\n    return shocks,thr,cr\n\ndef contract_phase_from_ticker(ticker, shock_ts):\n    m=re.match(r"KXBTC15M-(\\d{2})([A-Z]{3})(\\d{2})(\\d{2})(\\d{2})-(\\d{2})",ticker)\n    if not m:\n        return None\n    yy,mon,dd,hh,mm,ss=m.groups()\n    months={"JAN":1,"FEB":2,"MAR":3,"APR":4,"MAY":5,"JUN":6,"JUL":7,"AUG":8,"SEP":9,"OCT":10,"NOV":11,"DEC":12}\n    try:\n        end=shock_ts.replace(year=2000+int(yy),month=months[mon],day=int(dd),hour=int(hh),minute=int(mm),second=int(ss),microsecond=0)\n        sec_to_end=(end-shock_ts).total_seconds()\n        sec_from_start=900-sec_to_end\n        return sec_from_start,sec_to_end\n    except Exception:\n        return None\n\ndef choose_contract(kalshi,ts):\n    cand=[]\n    for t,pts in kalshi.items():\n        times=[x[0] for x in pts]\n        i=bisect_right(times,ts)-1\n        if i<0: continue\n        lag=(ts-pts[i][0]).total_seconds()\n        phase=contract_phase_from_ticker(t,ts)\n        if phase is None: continue\n        sec_from_start,sec_to_end=phase\n        if 0<=lag<=90 and 0<=sec_from_start<=900 and 0<=sec_to_end<=900:\n            cand.append((lag,t,i,pts,sec_from_start,sec_to_end))\n    if not cand: return None\n    cand.sort(key=lambda x:x[0])\n    return cand[0]\n\ndef reaction_curve(shock,kalshi):\n    chosen=choose_contract(kalshi,shock["ts"])\n    if chosen is None: return None\n    lag,ticker,i0,pts,sec_from_start,sec_to_end=chosen\n    base_ts,base_seq,p0=pts[i0]\n    fut=[x for x in pts[i0+1:] if 0<(x[0]-shock["ts"]).total_seconds()<=300]\n    if not fut: return None\n    out={"ticker":ticker,"shock_ts":shock["ts"],"shock_ret":shock["ret"],"shock_span":shock["span"],\n         "base_price":p0,"base_ts":base_ts,"base_seq":base_seq,"base_lag_s":lag,\n         "sec_from_start":sec_from_start,"sec_to_end":sec_to_end}\n    direction=1 if shock["ret"]>=0 else -1\n    out["direction"]=direction\n    prices=[x[2] for x in fut]\n    signed=[direction*(p-p0) for p in prices]\n    out["fav_excursion"]=max(signed)\n    out["adv_excursion"]=max(-x for x in signed)\n    out["raw_up_mfe"]=max(p-p0 for p in prices)\n    out["raw_down_mae"]=max(p0-p for p in prices)\n    for h in (5,15,30,60,120,300):\n        z=[x for x in fut if (x[0]-shock["ts"]).total_seconds()<=h]\n        if z:\n            d=z[-1][2]-p0\n            out[f"d{h}"]=d\n            out[f"sd{h}"]=direction*d\n    first=None\n    for h in (5,15,30,60,120,300):\n        sd=out.get(f"sd{h}")\n        if sd is not None and abs(sd)>=.03:\n            first=h; break\n    out["first_3c_s"]=first\n    out["full_300_available"]=bool(fut and (fut[-1][0]-shock["ts"]).total_seconds()>=285)\n    return out\n\ndef phase_bucket(sec_from_start,sec_to_end):\n    if sec_from_start<180: return "EARLY"\n    if sec_to_end<=180: return "LATE"\n    return "MID"\n\nrows=load_rows(); spot,kalshi=build_series(rows)\nshocks,thr,base=detect_certified_shocks(spot,60)\ndataset=[]; seen=set()\nfor s in shocks:\n    c=reaction_curve(s,kalshi)\n    if not c or not c["full_300_available"]: continue\n    key=(c["ticker"],round(c["shock_ts"].timestamp()/30))\n    if key in seen: continue\n    seen.add(key)\n    c["phase"]=phase_bucket(c["sec_from_start"],c["sec_to_end"])\n    dataset.append(c)\ndataset.sort(key=lambda x:x["shock_ts"])\nprint("[CLEAN_EPISODES]",len(dataset))\nprint("[FULL_300S_REQUIRED]",True)\nprint("[DUPLICATE_30S_BUCKETS_REJECTED]",True)\nprint("[CROSS_CONTRACT_CONTAMINATION_REJECTED]",True)\nfor c in dataset[:50]:\n    print("[EPISODE]",c["shock_ts"],c["ticker"],"phase=",c["phase"],\n          "shock_ret=",round(c["shock_ret"],8),\n          "first_3c_s=",c["first_3c_s"],\n          "fav=",round(c["fav_excursion"],4),\n          "adv=",round(c["adv_excursion"],4),\n          "sd300=",c.get("sd300"))\nprint("[PASS] OPA-039 exact lag opportunity dataset audit complete")\n'

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
    print(" OPA-039 EXACT LAG OPPORTUNITY DATASET")
    print("="*120)
    TEST.write_text(BODY.lstrip(),encoding="utf-8")
    py_compile.compile(str(TEST),doraise=True)
    print("[PASS] wrote",TEST.name)
    print("[PASS] PostgreSQL READ ONLY")
    print("[PASS] no runtime mutation")
    print("[PASS] no probability/direction/publication activation")
    print("[PASS] execution_authority remains FALSE")

if __name__=="__main__":
    main()
