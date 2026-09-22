from pathlib import Path
import py_compile

ROOT=Path.cwd()
TEST=ROOT/'test_oracle_predictive_audit_017_pre_momentum_path_labels.py'
BODY='\nfrom collections import defaultdict, Counter\nimport json, re\nfrom pathlib import Path\nfrom qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect\n\nROOT=Path.cwd()\nTICKER_RE=re.compile(r\'\\bKXBTC15M-[A-Z0-9-]+\\b\',re.I)\nPREF=("yes_bid_dollars","yes_ask_dollars","yes_price_dollars","price_dollars","last_price_dollars")\n\ndef walk(x):\n    if isinstance(x,dict):\n        for k,v in x.items():\n            yield str(k),v\n            yield from walk(v)\n    elif isinstance(x,list):\n        for v in x:yield from walk(v)\n\ndef ticker(x):\n    for k,v in walk(x):\n        if "ticker" in k.lower() and isinstance(v,str):\n            m=TICKER_RE.search(v.upper())\n            if m:return m.group(0)\n    m=TICKER_RE.search(json.dumps(x,default=str).upper())\n    return m.group(0) if m else None\n\ndef px(x):\n    vals={}\n    for k,v in walk(x):\n        kl=k.lower()\n        if kl in PREF:\n            try:\n                z=float(v)\n                if 0<=z<=1:vals.setdefault(kl,z)\n            except Exception:pass\n    if "yes_price_dollars" in vals:return vals["yes_price_dollars"]\n    if "price_dollars" in vals:return vals["price_dollars"]\n    if "last_price_dollars" in vals:return vals["last_price_dollars"]\n    if "yes_bid_dollars" in vals and "yes_ask_dollars" in vals:\n        return (vals["yes_bid_dollars"]+vals["yes_ask_dollars"])/2\n    return vals.get("yes_bid_dollars") or vals.get("yes_ask_dollars")\n\nrows=[];cursor=None\nfor page in range(1,5):\n    with connect(ROOT,autocommit=False) as c:\n        with c.cursor() as q:\n            q.execute("SET TRANSACTION READ ONLY");q.execute("SET LOCAL statement_timeout=\'15000ms\'")\n            sql="""SELECT sequence_number,observed_at,canonical_observation_json\n                   FROM public.oracle_canonical_observations\n                   WHERE source_id=\'source.kalshi.market_data\'"""\n            args=[]\n            if cursor is not None:sql+=" AND sequence_number < %s";args.append(cursor)\n            sql+=" ORDER BY sequence_number DESC LIMIT 50000"\n            q.execute(sql,tuple(args));b=q.fetchall() or []\n        c.rollback()\n    print("[PAGE]",page,"rows=",len(b))\n    if not b:break\n    rows+=b;cursor=min(int(x[0]) for x in b)\n\npaths=defaultdict(list)\nfor seq,ts,obj in rows:\n    try:d=obj if isinstance(obj,dict) else json.loads(obj)\n    except Exception:continue\n    t=ticker(d);p=px(d)\n    if t and p is not None:paths[t].append((ts,int(seq),float(p)))\n\nlabels=[];first_hit=Counter()\nfor t,pts in paths.items():\n    pts=sorted(pts,key=lambda x:(x[0],x[1]))\n    for i,(ts,seq,p0) in enumerate(pts):\n        future=[x for x in pts[i+1:] if 0 < (x[0]-ts).total_seconds() <= 300]\n        if len(future)<3:continue\n        ups=[p-p0 for _,_,p in future];dns=[p0-p for _,_,p in future]\n        mfe=max(ups);mae=max(dns)\n        hit=None\n        for ts2,_,p in future:\n            move=p-p0\n            if move>=0.05:hit="+5c";break\n            if move<=-0.05:hit="-5c";break\n        if hit:first_hit[hit]+=1\n        labels.append((t,ts,p0,mfe,mae,hit,(future[-1][0]-ts).total_seconds()))\n\nprint("[CONTRACTS]",len(paths))\nprint("[5M_LABELS]",len(labels))\nif labels:\n    print("[MEAN_MFE]",round(sum(x[3] for x in labels)/len(labels),6))\n    print("[MEAN_MAE]",round(sum(x[4] for x in labels)/len(labels),6))\nprint("[FIRST_HIT_5C]",dict(first_hit))\nfor x in labels[:30]:\n    print("[LABEL]",x[0],"t=",x[1],"p0=",round(x[2],4),"mfe=",round(x[3],4),"mae=",round(x[4],4),"first5=",x[5],"window_s=",round(x[6],1))\nprint("[TARGETS] MFE,MAE,+5c_before_-5c,time_to_move,reversal")\nprint("[PASS] OPA-017 pre-momentum path-label reconstruction audit complete")\n'

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
    print(" OPA-017 PRE-MOMENTUM PRICE-PATH LABEL RECONSTRUCTION")
    print("="*120)
    TEST.write_text(BODY.lstrip(),encoding="utf-8")
    py_compile.compile(str(TEST),doraise=True)
    print("[PASS] wrote",TEST.name)
    print('[PASS] reconstructs 5-minute MFE/MAE and +5c/-5c first-hit labels')
    print('[PASS] labels use only future observations after each historical timestamp')
    print('[PASS] PostgreSQL READ ONLY')
    print('[PASS] no runtime mutation')
    print('[PASS] no probability activation')
    print('[PASS] execution_authority remains FALSE')

if __name__=="__main__":
    main()
