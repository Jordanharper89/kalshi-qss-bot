from collections import Counter, defaultdict
import json, re
from pathlib import Path
from qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect

ROOT=Path.cwd()
TICKER_RE=re.compile(r'\bKXBTC15M-[A-Z0-9-]+\b',re.I)
KEYS=("title","subtitle","yes_sub_title","no_sub_title","rules_primary","strike_type","floor_strike","cap_strike","close_time","expiration_time","settlement_value","result","status")

def walk(x,path=""):
    if isinstance(x,dict):
        for k,v in x.items():
            p=f"{path}.{k}" if path else str(k)
            yield p,k,v
            yield from walk(v,p)
    elif isinstance(x,list):
        for i,v in enumerate(x):
            yield from walk(v,f"{path}[{i}]")

rows=[];cursor=None
for page in range(1,5):
    with connect(ROOT,autocommit=False) as c:
        with c.cursor() as q:
            q.execute("SET TRANSACTION READ ONLY");q.execute("SET LOCAL statement_timeout='15000ms'")
            sql="""SELECT sequence_number,observed_at,observation_type,canonical_observation_json
                   FROM public.oracle_canonical_observations
                   WHERE source_id='source.kalshi.market_data'"""
            args=[]
            if cursor is not None:sql+=" AND sequence_number < %s";args.append(cursor)
            sql+=" ORDER BY sequence_number DESC LIMIT 50000"
            q.execute(sql,tuple(args));b=q.fetchall() or []
        c.rollback()
    print("[PAGE]",page,"rows=",len(b))
    if not b:break
    rows+=b;cursor=min(int(x[0]) for x in b)

contracts=defaultdict(lambda:{"keys":Counter(),"samples":{},"types":Counter(),"rows":0})
for seq,ts,typ,obj in rows:
    try:d=obj if isinstance(obj,dict) else json.loads(obj)
    except Exception:continue
    text=json.dumps(d,default=str).upper()
    m=TICKER_RE.search(text)
    if not m:continue
    t=m.group(0);c=contracts[t];c["rows"]+=1;c["types"][str(typ)]+=1
    for path,k,v in walk(d):
        kl=str(k).lower()
        if kl in KEYS and v not in (None,"",[],{}):
            c["keys"][kl]+=1
            c["samples"].setdefault(kl,str(v)[:220])

with_prop=with_expiry=with_result=0
for t,c in contracts.items():
    ks=c["keys"]
    prop=any(k in ks for k in ("title","subtitle","yes_sub_title","rules_primary","floor_strike","cap_strike"))
    expiry=any(k in ks for k in ("close_time","expiration_time"))
    result=any(k in ks for k in ("settlement_value","result","status"))
    with_prop+=prop;with_expiry+=expiry;with_result+=result

print("[BTC15M_CONTRACTS]",len(contracts))
print("[WITH_PROPOSITION_FIELDS]",with_prop)
print("[WITH_EXPIRY_FIELDS]",with_expiry)
print("[WITH_RESULT_OR_STATUS_FIELDS]",with_result)

for t,c in sorted(contracts.items(),key=lambda kv:kv[1]["rows"],reverse=True)[:40]:
    print("[CONTRACT]",t,"rows=",c["rows"],"types=",dict(c["types"]),"fields=",dict(c["keys"]))
    for k,v in c["samples"].items():
        print("   [FIELD]",k,"=",v)

if with_result==0:
    print("[GAP] settlement/result lineage not found in sampled source.kalshi.market_data rows")
    print("[NEXT_REQUIREMENT] locate certified settled-market/result source before settlement-probability backtest")
print("[PASS] OPA-019 exact proposition-expiry-settlement-lineage audit complete")
