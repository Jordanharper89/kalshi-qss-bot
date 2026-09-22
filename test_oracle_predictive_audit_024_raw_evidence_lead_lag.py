from bisect import bisect_right
from collections import defaultdict,Counter
import json
from pathlib import Path
from qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect

ROOT=Path.cwd()
RAW_PREFIXES=("source.crypto.condition.btc.coinbase.","source.crypto.condition.btc.bitcoin.")

def text(x):
    try: return json.dumps(x if isinstance(x,(dict,list)) else json.loads(x),default=str)
    except Exception: return str(x)

rows=[];cursor=None
for page in range(1,5):
    with connect(ROOT,autocommit=False) as c:
        with c.cursor() as q:
            q.execute("SET TRANSACTION READ ONLY"); q.execute("SET LOCAL statement_timeout='15000ms'")
            sql="SELECT sequence_number,observed_at,source_id,observation_type,canonical_observation_json FROM public.oracle_canonical_observations"
            args=[]
            if cursor is not None: sql+=" WHERE sequence_number < %s"; args.append(cursor)
            sql+=" ORDER BY sequence_number DESC LIMIT 50000"
            q.execute(sql,tuple(args)); b=q.fetchall() or []
        c.rollback()
    print("[PAGE]",page,"rows=",len(b))
    if not b: break
    rows+=b; cursor=min(int(x[0]) for x in b)

kal=[]; raw=defaultdict(list)
for seq,ts,source,typ,obj in rows:
    if ts is None: continue
    s=str(source)
    if s=="source.kalshi.market_data" and "KXBTC15M-" in text(obj).upper():
        kal.append((ts,int(seq),str(typ)))
    elif s.startswith(RAW_PREFIXES):
        raw[s].append((ts,int(seq),str(typ)))

for s in raw: raw[s].sort()
raw_times={s:[x[0] for x in arr] for s,arr in raw.items()}
kal.sort()
available=Counter(); examples=[]
for kts,kseq,ktyp in kal:
    present=[]
    for s,arr in raw.items():
        idx=bisect_right(raw_times[s],kts)-1
        if idx>=0:
            lag=(kts-arr[idx][0]).total_seconds()
            if 0<=lag<=60: present.append((s,lag,arr[idx]))
    if present:
        available["any_raw_within_60s"]+=1
        if any(x[1]<=30 for x in present): available["any_raw_within_30s"]+=1
        if any(x[1]<=15 for x in present): available["any_raw_within_15s"]+=1
        if any(x[1]<=5 for x in present): available["any_raw_within_5s"]+=1
        if len(examples)<40: examples.append((kts,kseq,sorted(present,key=lambda x:x[1])[:5]))

print("[KALSHI_BTC15M_ROWS]",len(kal))
print("[RAW_STREAM_COUNT]",len(raw))
print("[RAW_PAST_ONLY_COVERAGE]",dict(available))
for kts,kseq,p in examples:
    print("[ALIGN]",kts,"kalshi_seq=",kseq)
    for s,lag,row in p: print("   [RAW]",s,"lag_s=",round(lag,3),"observed_at=",row[0],"seq=",row[1],"type=",row[2])
print("[RULE] only raw Coinbase/Bitcoin observations may count as external pre-momentum evidence")
print("[PASS] OPA-024 raw-evidence lead/lag availability audit complete")
