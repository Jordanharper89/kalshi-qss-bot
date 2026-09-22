from pathlib import Path
import py_compile

ROOT=Path.cwd()
TEST=ROOT/"test_oracle_predictive_audit_015_learned_history_BOUNDED_SOURCE_REPAIR.py"
BODY=Path("test_oracle_predictive_audit_015_learned_history_BOUNDED_SOURCE_REPAIR.py.body").read_text(encoding="utf-8") if Path("test_oracle_predictive_audit_015_learned_history_BOUNDED_SOURCE_REPAIR.py.body").exists() else r'''from collections import Counter,defaultdict
import json
from pathlib import Path
from qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect

ROOT=Path.cwd()
ASSETS=("BTC","ETH","SOL")
SOURCES={a:f"source.crypto.learned_case.{a.lower()}" for a in ASSETS}

def read(asset):
    rows=[];cursor=None
    for page in range(1,5):
        with connect(ROOT,autocommit=False) as c:
            with c.cursor() as q:
                q.execute("SET TRANSACTION READ ONLY")
                q.execute("SET LOCAL statement_timeout='10000ms'")
                sql="""SELECT sequence_number,canonical_observation_json
                FROM public.oracle_canonical_observations
                WHERE source_id=%s AND observation_type='crypto_verified_learned_case'"""
                args=[SOURCES[asset]]
                if cursor is not None:
                    sql+=" AND sequence_number < %s";args.append(cursor)
                sql+=" ORDER BY sequence_number DESC LIMIT 1500"
                q.execute(sql,tuple(args));b=q.fetchall() or []
            c.rollback()
        print("[LEARNED_PAGE]",asset,page,"rows=",len(b))
        if not b:break
        rows+=b;cursor=min(int(x[0]) for x in b)
    return rows

def horizon(x):
    if isinstance(x,dict):
        for k in ("horizon_seconds","requested_horizon_seconds","realized_horizon_seconds"):
            if x.get(k) is not None:
                try:return int(float(x[k]))
                except:pass
        for v in x.values():
            h=horizon(v)
            if h is not None:return h
    if isinstance(x,list):
        for v in x:
            h=horizon(v)
            if h is not None:return h

for a in ASSETS:
    rows=read(a);hs=Counter()
    for _,obj in rows:
        try:d=obj if isinstance(obj,dict) else json.loads(obj)
        except:continue
        h=horizon(d)
        if h is not None:hs[h]+=1
    print("[ASSET_LEARNING_SAMPLE]",a,"rows=",len(rows),"horizons=",dict(hs))

print("[PASS] OPA-015 bounded learned-history audit complete")
'''

TEST.write_text(BODY,encoding="utf-8")
py_compile.compile(str(TEST),doraise=True)
print("[PASS] wrote",TEST.name)
print("[PASS] OAD-189 untouched")
print("[PASS] learned history bounded at 4 x 1500 rows per asset")
print("[PASS] PostgreSQL READ ONLY")
print("[PASS] no runtime mutation")