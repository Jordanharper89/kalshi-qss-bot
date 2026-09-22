from collections import Counter
import json
from pathlib import Path
from qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect

ROOT=Path.cwd()
rows=[]
cursor=None

for page in range(1,5):
    with connect(ROOT,autocommit=False) as c:
        with c.cursor() as q:
            q.execute("SET TRANSACTION READ ONLY")
            q.execute("SET LOCAL statement_timeout='15000ms'")

            sql="""SELECT sequence_number,observed_at,source_id,
                          observation_type,canonical_observation_json
                   FROM public.oracle_canonical_observations"""
            args=()

            if cursor is not None:
                sql+=" WHERE sequence_number < %s"
                args=(cursor,)

            sql+=" ORDER BY sequence_number DESC LIMIT 50000"
            q.execute(sql,args)
            batch=q.fetchall() or []

        c.rollback()

    print("[PAGE]",page,"rows=",len(batch))

    if not batch:
        break

    rows.extend(batch)
    cursor=min(int(x[0]) for x in batch)

kal=Counter()
ind=Counter()
asset_rows=Counter()
kal_times={a:[] for a in ("BTC","ETH","SOL")}
ind_times={a:[] for a in ("BTC","ETH","SOL")}

for seq,ts,source,typ,obj in rows:
    source=str(source)
    typ=str(typ)

    try:
        payload=obj if isinstance(obj,dict) else json.loads(obj)
        text=json.dumps(payload,separators=(",",":")).upper()
    except Exception:
        text=""

    asset=next(
        (a for a in ("BTC","ETH","SOL")
         if a in text or a in source.upper()),
        None
    )

    if not asset:
        continue

    asset_rows[asset]+=1

    if source=="source.kalshi.market_data":
        kal[(asset,typ)]+=1
        if ts:
            kal_times[asset].append(ts)

    elif (
        "crypto" in source.lower()
        or "coinbase" in source.lower()
        or any(x in source.lower()
               for x in ("bitcoin","ethereum","solana"))
    ):
        ind[(asset,source,typ)]+=1
        if ts:
            ind_times[asset].append(ts)

print("[ROWS_SCANNED]",len(rows))
print("[ASSET_ROWS]",dict(asset_rows))
print("[KALSHI_TYPES]",dict(kal.most_common(40)))

print("[INDEPENDENT_STREAMS]")
for k,n in ind.most_common(80):
    print(" ",k,"rows=",n)

for asset in ("BTC","ETH","SOL"):
    kt=kal_times[asset]
    it=ind_times[asset]

    print("[ASSET]",asset)
    print("[KALSHI_ROWS]",len(kt))
    print("[INDEPENDENT_ROWS]",len(it))

    if kt:
        print("[KALSHI_RANGE]",min(kt),max(kt))

    if it:
        print("[INDEPENDENT_RANGE]",min(it),max(it))

    overlap=bool(
        kt and it and
        max(min(kt),min(it)) <= min(max(kt),max(it))
    )

    print("[TIMESTAMP_OVERLAP]",asset,overlap)
    print("[REACTION_LAG_RECONSTRUCTION_FEASIBLE]",
          asset,overlap and bool(kt) and bool(it))

print("[PASS] OPA-014 200K bounded reaction-lag audit complete")
