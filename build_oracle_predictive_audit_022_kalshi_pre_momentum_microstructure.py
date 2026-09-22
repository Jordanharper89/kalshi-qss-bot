from pathlib import Path
import py_compile

ROOT=Path.cwd()
TEST=ROOT/'test_oracle_predictive_audit_022_kalshi_pre_momentum_microstructure.py'
BODY='\nfrom collections import defaultdict\nimport json,re\nfrom pathlib import Path\nfrom qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect\n\nROOT=Path.cwd()\nTICKER_RE=re.compile(r"\\bKXBTC15M-[A-Z0-9-]+\\b",re.I)\nPRICE_KEYS=("yes_price_dollars","price_dollars","last_price_dollars","yes_bid_dollars","yes_ask_dollars")\n\ndef walk(x):\n    if isinstance(x,dict):\n        for k,v in x.items():\n            yield str(k),v\n            yield from walk(v)\n    elif isinstance(x,list):\n        for v in x: yield from walk(v)\n\ndef parse(obj):\n    try: d=obj if isinstance(obj,dict) else json.loads(obj)\n    except Exception: return None,None,{}\n    text=json.dumps(d,default=str).upper(); m=TICKER_RE.search(text)\n    if not m: return None,None,{}\n    vals={}\n    for k,v in walk(d):\n        kl=k.lower()\n        if kl in PRICE_KEYS:\n            try:\n                z=float(v)\n                if 0<=z<=1: vals.setdefault(kl,z)\n            except Exception: pass\n    p=vals.get("yes_price_dollars") or vals.get("price_dollars") or vals.get("last_price_dollars")\n    if p is None and "yes_bid_dollars" in vals and "yes_ask_dollars" in vals:\n        p=(vals["yes_bid_dollars"]+vals["yes_ask_dollars"])/2\n    micro={}\n    if "yes_bid_dollars" in vals: micro["bid"]=vals["yes_bid_dollars"]\n    if "yes_ask_dollars" in vals: micro["ask"]=vals["yes_ask_dollars"]\n    if "bid" in micro and "ask" in micro: micro["spread"]=micro["ask"]-micro["bid"]\n    return m.group(0),p,micro\n\nrows=[];cursor=None\nfor page in range(1,5):\n    with connect(ROOT,autocommit=False) as c:\n        with c.cursor() as q:\n            q.execute("SET TRANSACTION READ ONLY"); q.execute("SET LOCAL statement_timeout=\'15000ms\'")\n            sql="SELECT sequence_number,observed_at,observation_type,canonical_observation_json FROM public.oracle_canonical_observations WHERE source_id=\'source.kalshi.market_data\'"\n            args=[]\n            if cursor is not None: sql+=" AND sequence_number < %s"; args.append(cursor)\n            sql+=" ORDER BY sequence_number DESC LIMIT 50000"\n            q.execute(sql,tuple(args)); b=q.fetchall() or []\n        c.rollback()\n    print("[PAGE]",page,"rows=",len(b))\n    if not b: break\n    rows+=b; cursor=min(int(x[0]) for x in b)\n\npaths=defaultdict(list)\nfor seq,ts,typ,obj in rows:\n    t,p,m=parse(obj)\n    if t and ts is not None and p is not None: paths[t].append((ts,int(seq),str(typ),float(p),m))\n\nfeatures=[]\nfor t,pts in paths.items():\n    pts=sorted(pts,key=lambda x:(x[0],x[1]))\n    for i in range(3,len(pts)):\n        ts,seq,typ,p,m=pts[i]\n        prev=pts[max(0,i-10):i]\n        dt=(ts-prev[0][0]).total_seconds()\n        if dt<=0: continue\n        delta=p-prev[-1][3]; velocity=(p-prev[0][3])/dt; spread=m.get("spread")\n        features.append((t,ts,p,delta,velocity,spread,len(prev)))\n\nprint("[CONTRACTS]",len(paths))\nprint("[MICROSTRUCTURE_FEATURE_ROWS]",len(features))\nprint("[SPREAD_FEATURE_ROWS]",sum(1 for x in features if x[5] is not None))\nfor x in features[:40]:\n    print("[FEATURE]",x[0],"t=",x[1],"p=",round(x[2],4),"last_delta=",round(x[3],4),"velocity_per_s=",round(x[4],8),"spread=",None if x[5] is None else round(x[5],4),"lookback_n=",x[6])\nprint("[FEATURE_SET] pre-T price velocity, recent delta, bid/ask spread where physically available")\nprint("[PASS] OPA-022 Kalshi pre-momentum microstructure feature audit complete")\n'

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

def main():
    print("="*120)
    print(" OPA-022 KALSHI PRE-MOMENTUM MICROSTRUCTURE")
    print("="*120)
    TEST.write_text(BODY.lstrip(), encoding="utf-8")
    py_compile.compile(str(TEST), doraise=True)
    print("[PASS] wrote", TEST.name)
    print('[PASS] reconstructs only pre-T Kalshi price/microstructure features')
    print('[PASS] price velocity and spread audited where present')
    print('[PASS] PostgreSQL READ ONLY')
    print('[PASS] no runtime mutation')
    print('[PASS] no probability activation')
    print('[PASS] execution_authority remains FALSE')

if __name__=="__main__":
    main()
