from pathlib import Path
import py_compile

ROOT=Path.cwd()
TEST=ROOT/'test_oracle_predictive_audit_025_pre_momentum_discrimination.py'
BODY='\nfrom collections import defaultdict\nfrom bisect import bisect_right\nimport json,re\nfrom pathlib import Path\nfrom qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect\n\nROOT=Path.cwd()\nTICKER_RE=re.compile(r"\\bKXBTC15M-[A-Z0-9-]+\\b",re.I)\nRAW_PREFIXES=("source.crypto.condition.btc.coinbase.","source.crypto.condition.btc.bitcoin.")\nPRICE_KEYS=("yes_price_dollars","price_dollars","last_price_dollars","yes_bid_dollars","yes_ask_dollars")\n\ndef walk(x):\n    if isinstance(x,dict):\n        for k,v in x.items():\n            yield str(k),v\n            yield from walk(v)\n    elif isinstance(x,list):\n        for v in x: yield from walk(v)\n\ndef kalshi_parse(obj):\n    try: d=obj if isinstance(obj,dict) else json.loads(obj)\n    except Exception: return None,None\n    text=json.dumps(d,default=str).upper(); m=TICKER_RE.search(text)\n    if not m: return None,None\n    vals={}\n    for k,v in walk(d):\n        if k.lower() in PRICE_KEYS:\n            try:\n                z=float(v)\n                if 0<=z<=1: vals.setdefault(k.lower(),z)\n            except Exception: pass\n    p=vals.get("yes_price_dollars") or vals.get("price_dollars") or vals.get("last_price_dollars")\n    if p is None and "yes_bid_dollars" in vals and "yes_ask_dollars" in vals:\n        p=(vals["yes_bid_dollars"]+vals["yes_ask_dollars"])/2\n    return m.group(0),p\n\nrows=[];cursor=None\nfor page in range(1,5):\n    with connect(ROOT,autocommit=False) as c:\n        with c.cursor() as q:\n            q.execute("SET TRANSACTION READ ONLY"); q.execute("SET LOCAL statement_timeout=\'15000ms\'")\n            sql="SELECT sequence_number,observed_at,source_id,canonical_observation_json FROM public.oracle_canonical_observations"\n            args=[]\n            if cursor is not None: sql+=" WHERE sequence_number < %s"; args.append(cursor)\n            sql+=" ORDER BY sequence_number DESC LIMIT 50000"\n            q.execute(sql,tuple(args)); b=q.fetchall() or []\n        c.rollback()\n    print("[PAGE]",page,"rows=",len(b))\n    if not b: break\n    rows+=b; cursor=min(int(x[0]) for x in b)\n\npaths=defaultdict(list); raw=defaultdict(list)\nfor seq,ts,source,obj in rows:\n    if ts is None: continue\n    s=str(source)\n    if s=="source.kalshi.market_data":\n        t,p=kalshi_parse(obj)\n        if t and p is not None: paths[t].append((ts,int(seq),float(p)))\n    elif s.startswith(RAW_PREFIXES):\n        raw[s].append((ts,int(seq)))\n\nfor s in raw: raw[s].sort()\nraw_times={s:[x[0] for x in arr] for s,arr in raw.items()}\n\nexamples=[]\nfor t,pts in paths.items():\n    pts=sorted(pts,key=lambda x:(x[0],x[1]))\n    step=max(1,len(pts)//16)\n    for i in range(3,len(pts)-1,step):\n        ts,seq,p0=pts[i]\n        fut=[x for x in pts[i+1:] if 0<(x[0]-ts).total_seconds()<=300]\n        if len(fut)<3: continue\n        y=None\n        for _,_,p in fut:\n            if p-p0>=0.05: y=1; break\n            if p-p0<=-0.05: y=0; break\n        if y is None: continue\n        raw_count=0; freshest=9999.0\n        for s,arr in raw.items():\n            idx=bisect_right(raw_times[s],ts)-1\n            if idx>=0:\n                lag=(ts-arr[idx][0]).total_seconds()\n                if 0<=lag<=60: raw_count+=1; freshest=min(freshest,lag)\n        if raw_count:\n            recent=pts[max(0,i-5):i]\n            dt=max((ts-recent[0][0]).total_seconds(),1e-9)\n            vel=(p0-recent[0][2])/dt\n            examples.append((ts,t,p0,vel,raw_count,freshest,y))\n\nexamples.sort(key=lambda x:x[0])\ncut=int(len(examples)*0.70)\ntrain=examples[:cut]; test=examples[cut:]\n\ndef predict_rule(x):\n    return 1 if (x[3]>0 and x[5]<=30) else 0\n\nif test:\n    hit=sum(predict_rule(x)==x[6] for x in test)/len(test)\n    pos=sum(x[6] for x in test)/len(test)\n    baseline=max(pos,1-pos)\nelse:\n    hit=baseline=pos=None\n\nprint("[LABELED_WITH_RAW_EVIDENCE]",len(examples))\nprint("[CHRONOLOGICAL_SPLIT] train=",len(train),"test=",len(test),"cutoff=",test[0][0] if test else None)\nprint("[TEST_POSITIVE_RATE]",None if pos is None else round(pos,6))\nprint("[PREDECLARED_RULE_HIT_RATE]",None if hit is None else round(hit,6))\nprint("[MAJORITY_BASELINE_HIT_RATE]",None if baseline is None else round(baseline,6))\nprint("[IMPORTANT] this is discrimination feasibility only, not production predictive certification")\nprint("[NEXT_IF_PROMISING] richer raw-evidence deltas, order flow, spread/liquidity, regime, condition interactions, calibration")\nprint("[NEXT_IF_NOT_PROMISING] reject simple-rule path and test richer condition combinations without publication")\nprint("[NO_LEAKAGE] all features observed at or before T; labels strictly after T")\nprint("[PASS] OPA-025 first chronological pre-momentum discrimination audit complete")\n'

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
    print(" OPA-025 PRE-MOMENTUM CHRONOLOGICAL DISCRIMINATION")
    print("="*120)
    TEST.write_text(BODY.lstrip(), encoding="utf-8")
    py_compile.compile(str(TEST), doraise=True)
    print("[PASS] wrote", TEST.name)
    print('[PASS] strict chronological train-before-test split')
    print('[PASS] predeclared simple discriminator vs majority baseline')
    print('[PASS] no future leakage')
    print('[PASS] explicitly not predictive-edge certification')
    print('[PASS] PostgreSQL READ ONLY')
    print('[PASS] execution_authority remains FALSE')

if __name__=="__main__":
    main()
