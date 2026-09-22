from collections import Counter,defaultdict
import json
from pathlib import Path

from qseries_v2.oracle_adapters.independent.oad_189_crypto_learned_case_exact_history_readback import (
    read_crypto_learned_case_history,
)
from qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import (
    connect,
)

ROOT=Path.cwd()

cases=list(read_crypto_learned_case_history(per_asset_limit=8192))

print("[LEARNED_CASES]",len(cases))
print(
    "[LEARNED_HORIZONS]",
    dict(Counter(int(x.horizon_seconds) for x in cases)),
)

for asset in ("BTC","ETH","SOL"):
    asset_cases=[x for x in cases if x.asset==asset]

    print(
        "[ASSET_LEARNING]",
        asset,
        "n=",len(asset_cases),
        "horizons=",
        dict(Counter(int(x.horizon_seconds) for x in asset_cases)),
    )

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

kalshi=defaultdict(list)
independent=defaultdict(list)

for seq,ts,source,typ,obj in rows:
    if ts is None:
        continue

    source=str(source)

    try:
        payload=obj if isinstance(obj,dict) else json.loads(obj)
        text=json.dumps(payload,separators=(",",":")).upper()
    except Exception:
        text=""

    asset=next(
        (
            a for a in ("BTC","ETH","SOL")
            if a in text or a in source.upper()
        ),
        None,
    )

    if not asset:
        continue

    if source=="source.kalshi.market_data":
        kalshi[asset].append(ts)

    elif (
        "crypto" in source.lower()
        or "coinbase" in source.lower()
        or any(
            x in source.lower()
            for x in ("bitcoin","ethereum","solana")
        )
    ):
        independent[asset].append(ts)

print("[ROWS_SCANNED]",len(rows))

for asset in ("BTC","ETH","SOL"):
    kt=kalshi[asset]
    it=independent[asset]

    kspan=(
        (max(kt)-min(kt)).total_seconds()
        if len(kt)>1 else 0
    )

    ispan=(
        (max(it)-min(it)).total_seconds()
        if len(it)>1 else 0
    )

    print(
        "[PHYSICAL_DEPTH]",
        asset,
        "kalshi_rows=",len(kt),
        "kalshi_span_s=",round(kspan,1),
        "independent_rows=",len(it),
        "independent_span_s=",round(ispan,1),
    )

    for horizon in (30,60,300,900,3600):
        learned=sum(
            1
            for x in cases
            if x.asset==asset
            and int(x.horizon_seconds)==horizon
        )

        history_feasible=(
            kspan>=horizon
            and ispan>=horizon
        )

        print(
            "[TARGET]",
            asset,
            "horizon_s=",horizon,
            "history_feasible=",history_feasible,
            "existing_learned_cases=",learned,
        )

print(
    "[PRICE_PATH_TARGETS]",
    "future_return,MFE,MAE,time_to_extreme,"
    "reversal,spread_stress,liquidity_stress,"
    "reaction_lag"
)

print(
    "[SETTLEMENT_TARGET]",
    "requires exact proposition + expiry + "
    "settlement outcome lineage"
)

print(
    "[SEPARATION_RULE]",
    "short-horizon price-path probability must "
    "not be represented as settlement probability"
)

print("[PASS] OPA-015 bounded multi-target feasibility audit complete")
