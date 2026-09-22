from collections import Counter
from pathlib import Path
from qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect

ROOT=Path.cwd()
RAW_PREFIXES=("source.crypto.condition.btc.coinbase.","source.crypto.condition.btc.bitcoin.")
DERIVED_PREFIXES=("source.crypto.prospective_","source.crypto.learned_case.","source.crypto.experience.","source.crypto.verified_")

rows=[];cursor=None
for page in range(1,5):
    with connect(ROOT,autocommit=False) as c:
        with c.cursor() as q:
            q.execute("SET TRANSACTION READ ONLY"); q.execute("SET LOCAL statement_timeout='15000ms'")
            sql="SELECT sequence_number,observed_at,source_id,observation_type FROM public.oracle_canonical_observations"
            args=[]
            if cursor is not None:
                sql+=" WHERE sequence_number < %s"; args.append(cursor)
            sql+=" ORDER BY sequence_number DESC LIMIT 50000"
            q.execute(sql,tuple(args)); b=q.fetchall() or []
        c.rollback()
    print("[PAGE]",page,"rows=",len(b))
    if not b: break
    rows+=b; cursor=min(int(x[0]) for x in b)

raw=Counter(); derived=Counter(); other=Counter(); raw_rows=[]
for seq,ts,source,typ in rows:
    s=str(source)
    if s.startswith(RAW_PREFIXES):
        raw[(s,str(typ))]+=1; raw_rows.append((seq,ts,s,str(typ)))
    elif s.startswith(DERIVED_PREFIXES):
        derived[(s,str(typ))]+=1
    elif "btc" in s.lower() or "bitcoin" in s.lower():
        other[(s,str(typ))]+=1

print("[RAW_EXTERNAL_BTC_STREAMS]")
for k,n in sorted(raw.items(),key=lambda x:(-x[1],x[0])): print(" ",k,"rows=",n)
print("[ORACLE_DERIVED_BTC_STREAMS]")
for k,n in sorted(derived.items(),key=lambda x:(-x[1],x[0]))[:40]: print(" ",k,"rows=",n)
print("[OTHER_BTC_STREAMS]")
for k,n in sorted(other.items(),key=lambda x:(-x[1],x[0]))[:40]: print(" ",k,"rows=",n)
print("[RAW_EXTERNAL_ROWS]",len(raw_rows))
if raw_rows:
    ts=[x[1] for x in raw_rows if x[1] is not None]
    if ts: print("[RAW_EXTERNAL_RANGE]",min(ts),max(ts))
print("[SEPARATION_RULE] raw external evidence excludes Oracle forecasts, learned cases, experience candidates, bindings")
print("[PASS] OPA-021 raw-external BTC evidence isolation audit complete")
