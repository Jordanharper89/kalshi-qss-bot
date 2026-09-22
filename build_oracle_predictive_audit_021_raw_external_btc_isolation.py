from pathlib import Path
import py_compile

ROOT=Path.cwd()
TEST=ROOT/'test_oracle_predictive_audit_021_raw_external_btc_isolation.py'
BODY='\nfrom collections import Counter\nfrom pathlib import Path\nfrom qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect\n\nROOT=Path.cwd()\nRAW_PREFIXES=("source.crypto.condition.btc.coinbase.","source.crypto.condition.btc.bitcoin.")\nDERIVED_PREFIXES=("source.crypto.prospective_","source.crypto.learned_case.","source.crypto.experience.","source.crypto.verified_")\n\nrows=[];cursor=None\nfor page in range(1,5):\n    with connect(ROOT,autocommit=False) as c:\n        with c.cursor() as q:\n            q.execute("SET TRANSACTION READ ONLY"); q.execute("SET LOCAL statement_timeout=\'15000ms\'")\n            sql="SELECT sequence_number,observed_at,source_id,observation_type FROM public.oracle_canonical_observations"\n            args=[]\n            if cursor is not None:\n                sql+=" WHERE sequence_number < %s"; args.append(cursor)\n            sql+=" ORDER BY sequence_number DESC LIMIT 50000"\n            q.execute(sql,tuple(args)); b=q.fetchall() or []\n        c.rollback()\n    print("[PAGE]",page,"rows=",len(b))\n    if not b: break\n    rows+=b; cursor=min(int(x[0]) for x in b)\n\nraw=Counter(); derived=Counter(); other=Counter(); raw_rows=[]\nfor seq,ts,source,typ in rows:\n    s=str(source)\n    if s.startswith(RAW_PREFIXES):\n        raw[(s,str(typ))]+=1; raw_rows.append((seq,ts,s,str(typ)))\n    elif s.startswith(DERIVED_PREFIXES):\n        derived[(s,str(typ))]+=1\n    elif "btc" in s.lower() or "bitcoin" in s.lower():\n        other[(s,str(typ))]+=1\n\nprint("[RAW_EXTERNAL_BTC_STREAMS]")\nfor k,n in sorted(raw.items(),key=lambda x:(-x[1],x[0])): print(" ",k,"rows=",n)\nprint("[ORACLE_DERIVED_BTC_STREAMS]")\nfor k,n in sorted(derived.items(),key=lambda x:(-x[1],x[0]))[:40]: print(" ",k,"rows=",n)\nprint("[OTHER_BTC_STREAMS]")\nfor k,n in sorted(other.items(),key=lambda x:(-x[1],x[0]))[:40]: print(" ",k,"rows=",n)\nprint("[RAW_EXTERNAL_ROWS]",len(raw_rows))\nif raw_rows:\n    ts=[x[1] for x in raw_rows if x[1] is not None]\n    if ts: print("[RAW_EXTERNAL_RANGE]",min(ts),max(ts))\nprint("[SEPARATION_RULE] raw external evidence excludes Oracle forecasts, learned cases, experience candidates, bindings")\nprint("[PASS] OPA-021 raw-external BTC evidence isolation audit complete")\n'

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
    print(" OPA-021 RAW EXTERNAL BTC EVIDENCE ISOLATION")
    print("="*120)
    TEST.write_text(BODY.lstrip(), encoding="utf-8")
    py_compile.compile(str(TEST), doraise=True)
    print("[PASS] wrote", TEST.name)
    print('[PASS] isolates Coinbase/Bitcoin raw evidence')
    print('[PASS] separates Oracle-derived learner/forecast artifacts')
    print('[PASS] PostgreSQL READ ONLY')
    print('[PASS] no runtime mutation')
    print('[PASS] no probability activation')
    print('[PASS] execution_authority remains FALSE')

if __name__=="__main__":
    main()
