from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

from qseries_v2.oracle_execution.solana_atomic_executor import checkpoint22_cached_alt_latency_cutover as c22

MANIFEST=Path(
    "runtime_state/oracle/solana_atomic_executor/"
    "live_hot_book.json"
)

UNIVERSAL_CAPACITY=Path(
    "runtime_state/oracle/solana_atomic_executor/"
    "capacity_aware_warm_universe.json"
)

REGISTRY=Path(
    "runtime_state/oracle/solana_atomic_executor/"
    "multi_dlmm_pair_registry.json"
)


def _load(path):
    if not path.is_file():
        raise RuntimeError(
            "CHECKPOINT25_MISSING:"+str(path)
        )

    return json.loads(
        path.read_text(encoding="utf-8")
    )


def _expanded_registry():
    manifest=_load(MANIFEST)
    rows=list(manifest.get("rows") or [])
    universal=_load(UNIVERSAL_CAPACITY)
    universal_rows=list(universal.get("rows") or [])
    if not universal_rows:
        raise RuntimeError("CHECKPOINT25_UNIVERSAL_CAPACITY_EMPTY")
    universal_ids={
        str(x.get("identity") or (str(x.get("token"))+"|"+str(x.get("meteora_pool"))))
        for x in universal_rows
    }
    for row in rows:
        identity=str(row.get("identity") or (str(row.get("token"))+"|"+str(row.get("meteora_pool"))))
        if identity not in universal_ids:
            raise RuntimeError("CHECKPOINT25_HOT_PAIR_NOT_IN_UNIVERSAL:"+identity)
    print("[CHECKPOINT25_UNIVERSAL_HYDRATION] universal_pairs=%d hydration_pairs=%d scheduler_slice_separate=True"%(
        len(universal_rows),len(rows)
    ),flush=True)

    if not rows:
        raise RuntimeError(
            "CHECKPOINT25_EMPTY_MANIFEST"
        )

    identities=set()
    out=[]

    for row in rows:
        token=str(row["token"])
        pool=str(row["meteora_pool"])
        pair_key=token+"|"+pool

        if pair_key in identities:
            raise RuntimeError(
                "CHECKPOINT25_DUPLICATE_IDENTITY:"+pair_key
            )

        identities.add(pair_key)

        out.append({
            "pair_key":pair_key,
            "token":token,
            "pump_pool":str(row["pump_pool"]),
            "meteora_pool":pool,
            "selected_legacy":bool(row.get("retained")),
            "discovery_rank":len(out)+1,
            "reported_tvl":float(row.get("reported_tvl") or 0),
            "token_x":str(row["token_x"]),
            "token_y":str(row["token_y"]),
            "decimals_x":int(row["decimals_x"]),
            "decimals_y":int(row["decimals_y"]),
            "array_count":len(row.get("array_addresses") or []),
            "complete_quote_count":1,
            "partial_size_count":0,
            "best_direction":"UNMEASURED_AT_CUTOVER",
            "best_size_sol":0.0,
            "best_local_net_lamports":0,
            "best_local_bps":0.0,
            "gross_positive":False,
        })

    by_token={}

    for row in out:
        by_token[row["token"]]=(
            by_token.get(row["token"],0)+1
        )

    return {
        "revision":
            "CHECKPOINT11_MULTI_POOL_REGISTRY_V1",
        "observed_unix":
            time.time(),
        "identity":
            "token|meteora_pool",
        "source_pool_limit_per_token":
            100,
        "tokens":
            len(by_token),
        "ready_pair_count":
            len(out),
        "alternate_ready_count":
            sum(
                1
                for row in out
                if not row["selected_legacy"]
            ),
        "gross_positive_count":
            0,
        "failures":
            [],
        "rows":
            out,
        "execution_authority":
            False,
        "simulation":
            False,
        "broadcast":
            False,
        "temporary_runtime_cutover":
            True,
    }


def _atomic_write(path,payload):
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    tmp=path.with_suffix(
        path.suffix+".cp25.tmp"
    )

    tmp.write_text(
        json.dumps(
            payload,
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    tmp.replace(path)


def main():
    p=argparse.ArgumentParser()

    p.add_argument(
        "--seconds",
        type=float,
        default=3600.0,
    )

    args=p.parse_args()

    if args.seconds<=0:
        raise RuntimeError(
            "CHECKPOINT25_SECONDS_MUST_BE_POSITIVE"
        )

    expanded=_expanded_registry()

    original_bytes=(
        REGISTRY.read_bytes()
        if REGISTRY.is_file()
        else None
    )

    original_count=0

    if original_bytes is not None:
        try:
            original_count=len(
                json.loads(
                    original_bytes.decode("utf-8")
                ).get("rows") or []
            )
        except Exception:
            original_count=-1

    old_argv=list(sys.argv)

    print(
        "[CHECKPOINT25_REGISTRY_CUTOVER] "
        "original_pairs=%d expanded_pairs=%d "
        "identity=token|meteora_pool"
        %(
            original_count,
            len(expanded["rows"]),
        ),
        flush=True,
    )

    print(
        "[CHECKPOINT25_STATE_OWNER] "
        "multi_dlmm_pair_registry.json -> "
        "checkpoint12/15/17 native hydration",
        flush=True,
    )

    print(
        "[CHECKPOINT25_SCHEMA] "
        "revision=CHECKPOINT11_MULTI_POOL_REGISTRY_V1 "
        "row_key=pair_key",
        flush=True,
    )

    print(
        "[CHECKPOINT25_CHAIN] "
        "expanded_registry -> native_multi_pool_hydration -> "
        "pair_templates -> bidirectional_best_first -> "
        "canonical_ALT -> cached_ALT -> real_fee -> "
        "freshness -> signed_sim",
        flush=True,
    )

    print(
        "[CHECKPOINT25_HOT_PATH] "
        "registry_swap=startup_only restoration=finally",
        flush=True,
    )

    print(
        "[BROADCAST] disabled",
        flush=True,
    )

    try:
        _atomic_write(
            REGISTRY,
            expanded,
        )

        verify=_load(REGISTRY)
        actual_rows=list(
            verify.get("rows") or []
        )

        if (
            verify.get("revision")
            !="CHECKPOINT11_MULTI_POOL_REGISTRY_V1"
        ):
            raise RuntimeError(
                "CHECKPOINT25_REVISION_MISMATCH"
            )

        if (
            verify.get("identity")
            !="token|meteora_pool"
        ):
            raise RuntimeError(
                "CHECKPOINT25_IDENTITY_MISMATCH"
            )

        if len(actual_rows)!=len(expanded["rows"]):
            raise RuntimeError(
                "CHECKPOINT25_REGISTRY_WRITE_MISMATCH:"
                +str(len(actual_rows))
            )

        for row in actual_rows:
            expected=(
                str(row["token"])
                +"|"
                +str(row["meteora_pool"])
            )

            if row.get("pair_key")!=expected:
                raise RuntimeError(
                    "CHECKPOINT25_BAD_PAIR_KEY:"
                    +expected
                )

        print(
            "[CHECKPOINT25_REGISTRY_READY] "
            "pairs=%d pair_key_contract=True"
            %len(actual_rows),
            flush=True,
        )

        sys.argv=[
            old_argv[0],
            "--seconds",
            str(float(args.seconds)),
        ]

        return c22.main()

    finally:
        sys.argv=old_argv

        if original_bytes is None:
            try:
                REGISTRY.unlink()
            except FileNotFoundError:
                pass

        else:
            tmp=REGISTRY.with_suffix(
                REGISTRY.suffix+".restore.tmp"
            )

            tmp.write_bytes(
                original_bytes
            )

            tmp.replace(
                REGISTRY
            )

        restored=(
            "ABSENT"
            if original_bytes is None
            else str(original_count)
        )

        print(
            "[CHECKPOINT25_REGISTRY_RESTORED] "
            "original_pairs=%s"
            %restored,
            flush=True,
        )


if __name__=="__main__":
    raise SystemExit(main())
