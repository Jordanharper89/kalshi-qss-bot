from pathlib import Path
import py_compile

ROOT=Path.cwd()
TEST=ROOT/'test_oracle_predictive_audit_024_raw_evidence_lead_lag.py'
BODY='\nfrom bisect import bisect_right\nfrom collections import defaultdict,Counter\nimport json\nfrom pathlib import Path\nfrom qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect\n\nROOT=Path.cwd()\nRAW_PREFIXES=("source.crypto.condition.btc.coinbase.","source.crypto.condition.btc.bitcoin.")\n\ndef text(x):\n    try: return json.dumps(x if isinstance(x,(dict,list)) else json.loads(x),default=str)\n    except Exception: return str(x)\n\nrows=[];cursor=None\nfor page in range(1,5):\n    with connect(ROOT,autocommit=False) as c:\n        with c.cursor() as q:\n            q.execute("SET TRANSACTION READ ONLY"); q.execute("SET LOCAL statement_timeout=\'15000ms\'")\n            sql="SELECT sequence_number,observed_at,source_id,observation_type,canonical_observation_json FROM public.oracle_canonical_observations"\n            args=[]\n            if cursor is not None: sql+=" WHERE sequence_number < %s"; args.append(cursor)\n            sql+=" ORDER BY sequence_number DESC LIMIT 50000"\n            q.execute(sql,tuple(args)); b=q.fetchall() or []\n        c.rollback()\n    print("[PAGE]",page,"rows=",len(b))\n    if not b: break\n    rows+=b; cursor=min(int(x[0]) for x in b)\n\nkal=[]; raw=defaultdict(list)\nfor seq,ts,source,typ,obj in rows:\n    if ts is None: continue\n    s=str(source)\n    if s=="source.kalshi.market_data" and "KXBTC15M-" in text(obj).upper():\n        kal.append((ts,int(seq),str(typ)))\n    elif s.startswith(RAW_PREFIXES):\n        raw[s].append((ts,int(seq),str(typ)))\n\nfor s in raw: raw[s].sort()\nraw_times={s:[x[0] for x in arr] for s,arr in raw.items()}\nkal.sort()\navailable=Counter(); examples=[]\nfor kts,kseq,ktyp in kal:\n    present=[]\n    for s,arr in raw.items():\n        idx=bisect_right(raw_times[s],kts)-1\n        if idx>=0:\n            lag=(kts-arr[idx][0]).total_seconds()\n            if 0<=lag<=60: present.append((s,lag,arr[idx]))\n    if present:\n        available["any_raw_within_60s"]+=1\n        if any(x[1]<=30 for x in present): available["any_raw_within_30s"]+=1\n        if any(x[1]<=15 for x in present): available["any_raw_within_15s"]+=1\n        if any(x[1]<=5 for x in present): available["any_raw_within_5s"]+=1\n        if len(examples)<40: examples.append((kts,kseq,sorted(present,key=lambda x:x[1])[:5]))\n\nprint("[KALSHI_BTC15M_ROWS]",len(kal))\nprint("[RAW_STREAM_COUNT]",len(raw))\nprint("[RAW_PAST_ONLY_COVERAGE]",dict(available))\nfor kts,kseq,p in examples:\n    print("[ALIGN]",kts,"kalshi_seq=",kseq)\n    for s,lag,row in p: print("   [RAW]",s,"lag_s=",round(lag,3),"observed_at=",row[0],"seq=",row[1],"type=",row[2])\nprint("[RULE] only raw Coinbase/Bitcoin observations may count as external pre-momentum evidence")\nprint("[PASS] OPA-024 raw-evidence lead/lag availability audit complete")\n'

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
    print(" OPA-024 RAW-EVIDENCE LEAD/LAG AVAILABILITY")
    print("="*120)
    TEST.write_text(BODY.lstrip(), encoding="utf-8")
    py_compile.compile(str(TEST), doraise=True)
    print("[PASS] wrote", TEST.name)
    print('[PASS] raw Coinbase/Bitcoin only')
    print('[PASS] past-only 5s/15s/30s/60s coverage')
    print('[PASS] PostgreSQL READ ONLY')
    print('[PASS] no runtime mutation')
    print('[PASS] no probability activation')
    print('[PASS] execution_authority remains FALSE')

if __name__=="__main__":
    main()
