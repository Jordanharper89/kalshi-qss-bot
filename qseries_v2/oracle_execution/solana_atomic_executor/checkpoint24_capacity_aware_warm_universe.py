from __future__ import annotations

import argparse
import base64
import json
import time
import urllib.error
from pathlib import Path

from meteora_dlmm import PoolState

from qseries_v2.oracle_strategy_intelligence.solana_money.native_atomic_money_machine import core as c
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import live_account_stream as pd

INVENTORY=Path(
    "runtime_state/oracle/solana_atomic_executor/"
    "full_surface_replenishment_inventory.json"
)

OLD_REGISTRY=Path(
    "runtime_state/oracle/solana_atomic_executor/"
    "multi_dlmm_pair_registry.json"
)

OUT=Path(
    "runtime_state/oracle/solana_atomic_executor/"
    "capacity_aware_warm_universe.json"
)


def _read_json(path):
    if not path.is_file():
        raise RuntimeError(
            "CHECKPOINT24_MISSING:"+str(path)
        )

    return json.loads(
        path.read_text(encoding="utf-8")
    )


def _old_identities():
    if not OLD_REGISTRY.is_file():
        return set()

    payload=_read_json(OLD_REGISTRY)
    rows=payload.get("rows") or []

    out=set()

    for row in rows:
        token=row.get("token")
        pool=(
            row.get("meteora_pool")
            or row.get("pool")
        )

        if token and pool:
            out.add(str(token)+"|"+str(pool))

    return out


def _account_retry(addr):
    last=None

    for attempt in range(1,7):
        try:
            return c.account(addr)

        except urllib.error.HTTPError as exc:
            last=exc

            if getattr(exc,"code",None)!=429 or attempt>=6:
                raise

            delay=min(
                0.4*(2**(attempt-1)),
                4.0,
            )

            print(
                "[CHECKPOINT24_429] "
                "account=%s attempt=%d sleep=%.2fs"
                %(addr[:12],attempt,delay),
                flush=True,
            )

            time.sleep(delay)

    raise last if last else RuntimeError(
        "CHECKPOINT24_ACCOUNT_FAILED"
    )


def _arrays_retry(pool):
    last=None

    for attempt in range(1,7):
        try:
            return c.dlmm_arrays(pool)

        except urllib.error.HTTPError as exc:
            last=exc

            if getattr(exc,"code",None)!=429 or attempt>=6:
                raise

            delay=min(
                0.5*(2**(attempt-1)),
                4.0,
            )

            print(
                "[CHECKPOINT24_429] "
                "arrays=%s attempt=%d sleep=%.2fs"
                %(pool[:12],attempt,delay),
                flush=True,
            )

            time.sleep(delay)

    raise last if last else RuntimeError(
        "CHECKPOINT24_ARRAYS_FAILED"
    )


def _hydrate(row,pump_cache):
    token=str(row["token"])
    pump_pool=str(row["pump_pool"])
    pool=str(row["meteora_pool"])

    if pump_pool not in pump_cache:
        pd_raw,_=_account_retry(pump_pool)
        pp=c.decode_pump_pool(pd_raw)

        if pp["quote_mint"]!=c.WSOL:
            raise RuntimeError(
                "PUMP_NOT_SOL"
            )

        bd,_=_account_retry(pp["base_vault"])
        qd,_=_account_retry(pp["quote_vault"])

        pump_cache[pump_pool]={
            "base_vault":pp["base_vault"],
            "quote_vault":pp["quote_vault"],
            "base_reserve":
                pd._token_amount_from_raw(bd),
            "quote_reserve":
                pd._token_amount_from_raw(qd),
        }

    p=pump_cache[pump_pool]

    lb,_=_account_retry(pool)
    arrays=_arrays_retry(pool)

    token_x=str(row["token_x"])
    token_y=str(row["token_y"])

    ps=pd.PairState(
        token=token,
        pump_pool=pump_pool,
        meteora_pool=pool,
        token_x=token_x,
        token_y=token_y,
        decimals_x=int(row["decimals_x"]),
        decimals_y=int(row["decimals_y"]),
        pump_base_vault=p["base_vault"],
        pump_quote_vault=p["quote_vault"],
        pump_base_reserve=int(p["base_reserve"]),
        pump_quote_reserve=int(p["quote_reserve"]),
        lb_bytes=lb,
        arrays=list(arrays),
        dlmm_state=None,
    )

    ps.dlmm_state=PoolState.from_accounts(
        ps.lb_bytes,
        [x[2] for x in ps.arrays],
        decimals_x=ps.decimals_x,
        decimals_y=ps.decimals_y,
        lb_pair_key=c.b58d(ps.meteora_pool),
        exhaustive=True,
    )

    watched=list(
        dict.fromkeys(
            ps.watched_accounts()
        )
    )

    return ps,watched


def _priority(row,retained):
    identity=str(row["identity"])

    return (
        0 if identity in retained else 1,
        0 if row.get("source")=="MRIYA_HOT" else 1,
        float(
            row.get("source_age")
            if row.get("source_age") is not None
            else 1e18
        ),
        -float(row.get("reported_tvl") or 0),
        identity,
    )


def build(max_accounts=768):
    if max_accounts<64:
        raise RuntimeError(
            "CHECKPOINT24_ACCOUNT_BUDGET_TOO_SMALL"
        )

    inv=_read_json(INVENTORY)
    rows=list(inv.get("rows") or [])

    if not rows:
        raise RuntimeError(
            "CHECKPOINT24_EMPTY_INVENTORY"
        )

    retained=_old_identities()

    rows.sort(
        key=lambda row:_priority(
            row,
            retained,
        )
    )

    selected=[]
    selected_accounts=set()
    pump_cache={}
    failures={}
    hydrated=0

    print(
        "[CHECKPOINT24_START] "
        "inventory=%d retained=%d max_accounts=%d"
        %(len(rows),len(retained),max_accounts),
        flush=True,
    )

    for rank,row in enumerate(rows,1):
        identity=str(row["identity"])

        try:
            pair,watched=_hydrate(
                row,
                pump_cache,
            )
            hydrated+=1

        except Exception as exc:
            key=type(exc).__name__+":"+str(exc)

            failures[key]=failures.get(key,0)+1

            print(
                "[CHECKPOINT24_HYDRATE_SKIP] "
                "rank=%d pair=%s error=%s"
                %(rank,identity[:44],key[:180]),
                flush=True,
            )

            continue

        incremental=[
            a
            for a in watched
            if a not in selected_accounts
        ]

        if (
            len(selected_accounts)
            +len(incremental)
            >max_accounts
        ):
            print(
                "[CHECKPOINT24_CAPACITY_SKIP] "
                "rank=%d pair=%s incremental=%d "
                "used=%d budget=%d"
                %(
                    rank,
                    identity[:44],
                    len(incremental),
                    len(selected_accounts),
                    max_accounts,
                ),
                flush=True,
            )
            continue

        selected_accounts.update(
            incremental
        )

        selected.append({
            "identity":identity,
            "token":pair.token,
            "pump_pool":pair.pump_pool,
            "meteora_pool":pair.meteora_pool,
            "token_x":pair.token_x,
            "token_y":pair.token_y,
            "decimals_x":pair.decimals_x,
            "decimals_y":pair.decimals_y,
            "pump_base_vault":
                pair.pump_base_vault,
            "pump_quote_vault":
                pair.pump_quote_vault,
            "array_addresses":[
                str(x[1])
                for x in pair.arrays
            ],
            "watched_accounts":watched,
            "account_cost":
                len(incremental),
            "total_accounts_after":
                len(selected_accounts),
            "retained":
                identity in retained,
            "source":row.get("source"),
            "source_age":row.get("source_age"),
            "reported_tvl":
                float(row.get("reported_tvl") or 0),
        })

        print(
            "[CHECKPOINT24_SELECTED] "
            "rank=%d pair=%s retained=%s "
            "incremental=%d used=%d/%d arrays=%d"
            %(
                rank,
                identity[:44],
                identity in retained,
                len(incremental),
                len(selected_accounts),
                max_accounts,
                len(pair.arrays),
            ),
            flush=True,
        )

    selected_ids={
        row["identity"]
        for row in selected
    }

    retained_selected=len(
        retained & selected_ids
    )

    tokens=len({
        row["token"]
        for row in selected
    })

    payload={
        "revision":
            "CHECKPOINT24_CAPACITY_AWARE_WARM_UNIVERSE",
        "observed_unix":time.time(),
        "source_inventory_pairs":len(rows),
        "hydrated_pairs":hydrated,
        "selected_pairs":len(selected),
        "selected_tokens":tokens,
        "selected_accounts":len(selected_accounts),
        "max_accounts":int(max_accounts),
        "retained_requested":len(retained),
        "retained_selected":retained_selected,
        "identity":"token|meteora_pool",
        "rows":selected,
        "failures":failures,
        "policy":{
            "old_pairs_first":True,
            "mriya_recency_second":True,
            "reported_tvl_tiebreak_only":True,
            "no_hard_tvl_filter":True,
            "capacity_by_actual_unique_accounts":True,
            "replenishment_only":True,
            "broadcast":False,
        },
        "execution_authority":False,
        "broadcast":False,
    }

    out=Path.cwd()/OUT
    out.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    tmp=out.with_suffix(
        out.suffix+".tmp"
    )

    tmp.write_text(
        json.dumps(
            payload,
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    tmp.replace(out)

    print(
        "[CHECKPOINT24_SUMMARY] "
        "inventory=%d hydrated=%d selected_pairs=%d "
        "tokens=%d accounts=%d/%d retained=%d/%d"
        %(
            len(rows),
            hydrated,
            len(selected),
            tokens,
            len(selected_accounts),
            max_accounts,
            retained_selected,
            len(retained),
        ),
        flush=True,
    )

    print(
        "[CHECKPOINT24_OUTPUT] %s"
        %out,
        flush=True,
    )

    print("[BROADCAST] disabled",flush=True)

    return payload


def main():
    p=argparse.ArgumentParser()
    p.add_argument(
        "--max-accounts",
        type=int,
        default=768,
    )
    args=p.parse_args()

    build(args.max_accounts)


if __name__=="__main__":
    main()
