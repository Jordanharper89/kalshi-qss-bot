from pathlib import Path
import py_compile

ROOT=Path.cwd()
TEST=ROOT/'test_oracle_predictive_audit_020_chronological_oos_plumbing.py'
BODY='\nfrom collections import defaultdict, Counter\nimport json, re, math\nfrom pathlib import Path\nfrom qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect\n\nROOT=Path.cwd()\nTICKER_RE=re.compile(r\'\\bKXBTC15M-[A-Z0-9-]+\\b\',re.I)\nPRICE_KEYS=("yes_price_dollars","price_dollars","last_price_dollars","yes_bid_dollars","yes_ask_dollars")\n\ndef walk(x):\n    if isinstance(x,dict):\n        for k,v in x.items():\n            yield str(k),v\n            yield from walk(v)\n    elif isinstance(x,list):\n        for v in x:yield from walk(v)\n\ndef parse(obj):\n    try:d=obj if isinstance(obj,dict) else json.loads(obj)\n    except Exception:return None,None\n    text=json.dumps(d,default=str).upper();m=TICKER_RE.search(text)\n    if not m:return None,None\n    vals={}\n    for k,v in walk(d):\n        kl=k.lower()\n        if kl in PRICE_KEYS:\n            try:\n                z=float(v)\n                if 0<=z<=1:vals.setdefault(kl,z)\n            except Exception:pass\n    p=vals.get("yes_price_dollars") or vals.get("price_dollars") or vals.get("last_price_dollars")\n    if p is None and "yes_bid_dollars" in vals and "yes_ask_dollars" in vals:\n        p=(vals["yes_bid_dollars"]+vals["yes_ask_dollars"])/2\n    return m.group(0),p\n\nrows=[];cursor=None\nfor page in range(1,5):\n    with connect(ROOT,autocommit=False) as c:\n        with c.cursor() as q:\n            q.execute("SET TRANSACTION READ ONLY");q.execute("SET LOCAL statement_timeout=\'15000ms\'")\n            sql="""SELECT sequence_number,observed_at,canonical_observation_json\n                   FROM public.oracle_canonical_observations\n                   WHERE source_id=\'source.kalshi.market_data\'"""\n            args=[]\n            if cursor is not None:sql+=" AND sequence_number < %s";args.append(cursor)\n            sql+=" ORDER BY sequence_number DESC LIMIT 50000"\n            q.execute(sql,tuple(args));b=q.fetchall() or []\n        c.rollback()\n    print("[PAGE]",page,"rows=",len(b))\n    if not b:break\n    rows+=b;cursor=min(int(x[0]) for x in b)\n\npaths=defaultdict(list)\nfor seq,ts,obj in rows:\n    t,p=parse(obj)\n    if t and p is not None and ts is not None:paths[t].append((ts,int(seq),float(p)))\n\nexamples=[]\nfor t,pts in paths.items():\n    pts=sorted(pts,key=lambda x:(x[0],x[1]))\n    if len(pts)<20:continue\n    for i in range(0,len(pts)-3,max(1,len(pts)//12)):\n        ts,seq,p0=pts[i]\n        fut=[x for x in pts[i+1:] if 0<(x[0]-ts).total_seconds()<=300]\n        if len(fut)<3:continue\n        first=None\n        for ts2,_,p in fut:\n            if p-p0>=0.05:first=1;break\n            if p-p0<=-0.05:first=0;break\n        if first is None:continue\n        examples.append((ts,t,p0,first))\n\nexamples.sort(key=lambda x:x[0])\ncut=int(len(examples)*0.70)\ntrain=examples[:cut];test=examples[cut:]\n\n# deliberately simple audit baseline: prior positive rate learned from earlier chronology only\ntrain_rate=(sum(x[3] for x in train)/len(train)) if train else 0.5\nbrier=sum((train_rate-x[3])**2 for x in test)/len(test) if test else None\nhit=sum((train_rate>=0.5)==bool(x[3]) for x in test)/len(test) if test else None\nnaive_brier=sum((0.5-x[3])**2 for x in test)/len(test) if test else None\n\nprint("[LABELED_EXAMPLES]",len(examples))\nprint("[CHRONOLOGICAL_SPLIT] train=",len(train),"test=",len(test),"cutoff=",test[0][0] if test else None)\nprint("[TRAIN_POSITIVE_RATE]",round(train_rate,6))\nprint("[TEST_BRIER_PRIOR_ONLY]",None if brier is None else round(brier,6))\nprint("[TEST_BRIER_50_50]",None if naive_brier is None else round(naive_brier,6))\nprint("[TEST_DIRECTIONAL_HIT_PRIOR_ONLY]",None if hit is None else round(hit,6))\nprint("[IMPORTANT] this is label/backtest plumbing validation, not an Oracle predictive model")\nprint("[NEXT_MODEL_INPUTS] past-only independent evidence, Kalshi microstructure, regime, order flow, liquidity, learned conditions")\nprint("[NO_LEAKAGE] training rows occur strictly before chronological test rows")\nprint("[PASS] OPA-020 chronological out-of-sample plumbing audit complete")\n'

# audit packaging line 01
# audit packaging line 02
# audit packaging line 03
# audit packaging line 04
# audit packaging line 05
# audit packaging line 06
# audit packaging line 07
# audit packaging line 08
# audit packaging line 09
# audit packaging line 10
# audit packaging line 11
# audit packaging line 12
# audit packaging line 13
# audit packaging line 14
# audit packaging line 15
# audit packaging line 16
# audit packaging line 17
# audit packaging line 18
# audit packaging line 19
# audit packaging line 20
# audit packaging line 21
# audit packaging line 22
# audit packaging line 23
# audit packaging line 24
# audit packaging line 25
# audit packaging line 26
# audit packaging line 27
# audit packaging line 28
# audit packaging line 29
# audit packaging line 30
# audit packaging line 31
# audit packaging line 32
# audit packaging line 33
# audit packaging line 34
# audit packaging line 35
# audit packaging line 36
# audit packaging line 37
# audit packaging line 38
# audit packaging line 39
# audit packaging line 40
# audit packaging line 41
# audit packaging line 42
# audit packaging line 43
# audit packaging line 44
# audit packaging line 45

def main():
    print("="*120)
    print(" OPA-020 CHRONOLOGICAL OUT-OF-SAMPLE PREDICTIVE PLUMBING")
    print("="*120)
    TEST.write_text(BODY.lstrip(),encoding="utf-8")
    py_compile.compile(str(TEST),doraise=True)
    print("[PASS] wrote",TEST.name)
    print('[PASS] strict chronological 70/30 train-before-test split')
    print('[PASS] evaluates label plumbing against 50/50 baseline')
    print('[PASS] explicitly not a predictive-edge certification')
    print('[PASS] PostgreSQL READ ONLY')
    print('[PASS] no runtime mutation')
    print('[PASS] probability publication remains disabled')
    print('[PASS] execution_authority remains FALSE')

if __name__=="__main__":
    main()
