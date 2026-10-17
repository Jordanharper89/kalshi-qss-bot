from __future__ import annotations

import argparse
import json
import time
import urllib.error
from pathlib import Path

from qseries_v2.oracle_strategy_intelligence.solana_money.native_atomic_money_machine import core as c
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import engine

OUT=Path(
    "runtime_state/oracle/solana_atomic_executor/"
    "full_surface_replenishment_inventory.json"
)

WSOL=c.WSOL


def _mint(v):
    if isinstance(v,str):
        return v
    if isinstance(v,dict):
        return (
            v.get("address")
            or v.get("mint")
            or v.get("token_address")
        )
    return None


def _all_dlmm_for_token(token):
    url=(
        "https://dlmm.datapi.meteora.ag/"
        "pools?page=1&page_size=100&query="
        +token
    )

    last=None

    for attempt in range(1,7):
        try:
            payload=c.http(url)
            rows=(
                payload.get("data")
                if isinstance(payload,dict)
                else payload
            )

            out=[]

            for x in rows or []:
                tx=x.get("token_x") or x.get("tokenX") or {}
                ty=x.get("token_y") or x.get("tokenY") or {}

                mx=_mint(tx)
                my=_mint(ty)

                if {mx,my}!={WSOL,token}:
                    continue

                addr=(
                    x.get("address")
                    or x.get("pool_address")
                    or x.get("pubkey")
                )

                if not addr:
                    continue

                dx=(
                    int(tx.get("decimals",9))
                    if isinstance(tx,dict)
                    else 9
                )
                dy=(
                    int(ty.get("decimals",6))
                    if isinstance(ty,dict)
                    else 6
                )

                tvl=float(
                    x.get("tvl")
                    or x.get("liquidity")
                    or x.get("liquidity_usd")
                    or 0
                )

                out.append({
                    "address":str(addr),
                    "token_x":mx,
                    "token_y":my,
                    "decimals_x":dx,
                    "decimals_y":dy,
                    "reported_tvl":tvl,
                })

            dedup={x["address"]:x for x in out}

            return sorted(
                dedup.values(),
                key=lambda x:float(x["reported_tvl"]),
                reverse=True,
            )

        except urllib.error.HTTPError as exc:
            last=exc

            if getattr(exc,"code",None)!=429 or attempt>=6:
                raise

            delay=min(0.5*(2**(attempt-1)),4.0)

            print(
                "[CHECKPOINT23_429] "
                "token=%s attempt=%d sleep=%.2fs"
                %(token[:12],attempt,delay),
                flush=True,
            )

            time.sleep(delay)

    raise last if last else RuntimeError(
        "CHECKPOINT23_DLMM_DISCOVERY_FAILED"
    )


def _raw_candidates(root,max_raw):
    old_budget=engine.DISCOVERY_BUDGET
    old_core_max=getattr(c,"MAX_TOKENS",None)

    try:
        engine.DISCOVERY_BUDGET=max(
            int(max_raw),
            int(old_budget),
        )

        if old_core_max is not None:
            c.MAX_TOKENS=max(
                int(max_raw),
                int(old_core_max),
            )

        rows=engine.raw_candidate_universe(root)

        return list(rows)[:int(max_raw)]

    finally:
        engine.DISCOVERY_BUDGET=old_budget

        if old_core_max is not None:
            c.MAX_TOKENS=old_core_max


def build_inventory(max_raw=128):
    root=Path.cwd()
    raw=_raw_candidates(root,max_raw)

    identities={}
    failures={}
    exact_tokens=0

    print(
        "[CHECKPOINT23_RAW] candidates=%d max_raw=%d"
        %(len(raw),int(max_raw)),
        flush=True,
    )

    for i,row in enumerate(raw,1):
        token=str(row["token"])
        pump_pool=str(row["pump_pool"])

        ok,why=engine.exact_pool_ok(
            token,
            pump_pool,
        )

        if not ok:
            failures[why]=failures.get(why,0)+1
            continue

        try:
            pools=_all_dlmm_for_token(token)

        except Exception as exc:
            key=(
                "HTTP_429"
                if isinstance(exc,urllib.error.HTTPError)
                and getattr(exc,"code",None)==429
                else type(exc).__name__
            )

            failures[key]=failures.get(key,0)+1

            print(
                "[CHECKPOINT23_TOKEN_SKIP] "
                "token=%s error=%s:%s"
                %(token[:12],key,str(exc)[:180]),
                flush=True,
            )

            continue

        if not pools:
            failures["NO_DLMM_PAIR"]=(
                failures.get("NO_DLMM_PAIR",0)+1
            )
            continue

        exact_tokens+=1

        for meta in pools:
            identity=token+"|"+meta["address"]

            identities[identity]={
                "identity":identity,
                "token":token,
                "pump_pool":pump_pool,
                "meteora_pool":meta["address"],
                "token_x":meta["token_x"],
                "token_y":meta["token_y"],
                "decimals_x":int(meta["decimals_x"]),
                "decimals_y":int(meta["decimals_y"]),
                "reported_tvl":float(meta["reported_tvl"]),
                "source":row.get("source"),
                "source_age":row.get("age"),
            }

        print(
            "[CHECKPOINT23_TOKEN] "
            "rank=%d token=%s dlmm_pools=%d total_identities=%d"
            %(i,token[:12],len(pools),len(identities)),
            flush=True,
        )

    rows=list(identities.values())

    rows.sort(
        key=lambda x:(
            -float(x["reported_tvl"]),
            x["identity"],
        )
    )

    payload={
        "revision":"CHECKPOINT23_FULL_SURFACE_REPLENISHMENT_INVENTORY",
        "observed_unix":time.time(),
        "raw_candidates":len(raw),
        "exact_crosslisted_tokens":exact_tokens,
        "pair_identities":len(rows),
        "identity":"token|meteora_pool",
        "rows":rows,
        "failures":failures,
        "execution_authority":False,
        "broadcast":False,
        "notes":{
            "tvl_is_ranking_only":True,
            "hard_tvl_filter":False,
            "replenishment_only":True,
            "hot_execution_path_unchanged":True,
        },
    }

    out=root/OUT
    out.parent.mkdir(parents=True,exist_ok=True)

    tmp=out.with_suffix(out.suffix+".tmp")
    tmp.write_text(
        json.dumps(payload,indent=2,sort_keys=True),
        encoding="utf-8",
    )
    tmp.replace(out)

    print(
        "[CHECKPOINT23_SUMMARY] "
        "raw=%d exact_tokens=%d pair_identities=%d failures=%s"
        %(
            len(raw),
            exact_tokens,
            len(rows),
            json.dumps(failures,sort_keys=True),
        ),
        flush=True,
    )

    print(
        "[CHECKPOINT23_POLICY] "
        "replenishment_only=True hard_tvl_filter=False "
        "existing_pairs_retained_by_next_cutover=True",
        flush=True,
    )

    print(
        "[CHECKPOINT23_OUTPUT] %s"%out,
        flush=True,
    )

    print("[BROADCAST] disabled",flush=True)

    return payload


def main():
    p=argparse.ArgumentParser()
    p.add_argument(
        "--max-raw",
        type=int,
        default=128,
    )
    args=p.parse_args()

    if args.max_raw<1:
        raise RuntimeError(
            "CHECKPOINT23_MAX_RAW_MUST_BE_POSITIVE"
        )

    build_inventory(args.max_raw)


if __name__=="__main__":
    main()
