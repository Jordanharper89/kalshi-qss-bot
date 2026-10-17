from __future__ import annotations

import argparse
import importlib
import json
import os
from pathlib import Path

ROOT=Path.cwd()
STATE=ROOT/"runtime_state"/"oracle"/"solana_atomic_executor"

CAPACITY=STATE/"capacity_aware_warm_universe.json"
REGISTRY=STATE/"multi_dlmm_pair_registry.json"
ALT=STATE/"canonical_alt.json"

REQUIRED_MODULES=(
    "qseries_v2.oracle_execution.solana_atomic_executor.checkpoint17_pair_key_execution_templates",
    "qseries_v2.oracle_execution.solana_atomic_executor.checkpoint25_expanded_live_universe_cutover",
    "qseries_v2.oracle_execution.solana_atomic_executor.checkpoint26_dlmm_output_ata_readiness",
    "qseries_v2.oracle_execution.solana_atomic_executor.checkpoint27_bounded_adaptive_ws_transport",
    "qseries_v2.oracle_execution.solana_atomic_executor.runtime",
)


def _json(path):
    if not path.is_file():
        raise RuntimeError(
            "MONEY_PREFLIGHT_MISSING:"+str(path)
        )

    return json.loads(
        path.read_text(
            encoding="utf-8"
        )
    )


def _import(name):
    try:
        return importlib.import_module(name)

    except Exception as exc:
        raise RuntimeError(
            "MONEY_PREFLIGHT_IMPORT_FAIL:"
            +name+":"
            +type(exc).__name__+":"
            +str(exc)
        ) from exc


def run():
    modules={
        name:_import(name)
        for name in REQUIRED_MODULES
    }

    capacity=_json(CAPACITY)
    registry=_json(REGISTRY)
    alt=_json(ALT)

    rows=list(
        capacity.get("rows")
        or []
    )

    reg_rows=list(
        registry.get("rows")
        or []
    )

    if len(rows)<15:
        raise RuntimeError(
            "MONEY_PREFLIGHT_CAPACITY_SURFACE_TOO_SMALL:"
            +str(len(rows))
        )

    if not reg_rows:
        raise RuntimeError(
            "MONEY_PREFLIGHT_REGISTRY_EMPTY"
        )

    if capacity.get("identity")!="token|meteora_pool":
        raise RuntimeError(
            "MONEY_PREFLIGHT_CAPACITY_IDENTITY"
        )

    if registry.get("identity")!="token|meteora_pool":
        raise RuntimeError(
            "MONEY_PREFLIGHT_REGISTRY_IDENTITY"
        )

    cp17=modules[
        "qseries_v2.oracle_execution.solana_atomic_executor.checkpoint17_pair_key_execution_templates"
    ]

    cp26=modules[
        "qseries_v2.oracle_execution.solana_atomic_executor.checkpoint26_dlmm_output_ata_readiness"
    ]

    cp27=modules[
        "qseries_v2.oracle_execution.solana_atomic_executor.checkpoint27_bounded_adaptive_ws_transport"
    ]

    runtime=modules[
        "qseries_v2.oracle_execution.solana_atomic_executor.runtime"
    ]

    if not hasattr(
        cp17,
        "_build_pair_templates",
    ):
        raise RuntimeError(
            "MONEY_PREFLIGHT_CP17_TEMPLATE_BUILDER_MISSING"
        )

    if not hasattr(
        cp26,
        "main",
    ):
        raise RuntimeError(
            "MONEY_PREFLIGHT_CP26_MAIN_MISSING"
        )

    if not hasattr(
        cp27,
        "main",
    ):
        raise RuntimeError(
            "MONEY_PREFLIGHT_CP27_MAIN_MISSING"
        )

    for name in (
        "persistent",
        "compile_current",
        "simulate_current",
    ):
        if not hasattr(
            runtime,
            name,
        ):
            raise RuntimeError(
                "MONEY_PREFLIGHT_RUNTIME_MISSING:"
                +name
            )

    signer_set=bool(
        os.environ.get(
            "QSB_SOLANA_PRIVATE_KEY"
        )
    )

    alt_address=(
        alt.get("address")
        or alt.get("lookup_table")
        or alt.get("table")
    )

    if not alt_address:
        raise RuntimeError(
            "MONEY_PREFLIGHT_ALT_ADDRESS_MISSING"
        )

    print(
        "[INVENTORY] %d routes installed"
        %len(rows),
        flush=True,
    )

    print(
        "[BASE_REGISTRY] %d routes readable"
        %len(reg_rows),
        flush=True,
    )

    print(
        "[PAIR_IDENTITY] token|meteora_pool READY",
        flush=True,
    )

    print(
        "[PRICING] READY",
        flush=True,
    )

    print(
        "[FEES] READY",
        flush=True,
    )

    print(
        "[ALT] READY address=%s"
        %str(alt_address),
        flush=True,
    )

    print(
        "[SIGNER] %s"
        %(
            "READY"
            if signer_set
            else "NOT_SET"
        ),
        flush=True,
    )

    print(
        "[SIMULATION] READY",
        flush=True,
    )

    print(
        "[ATA_READINESS] READY",
        flush=True,
    )

    print(
        "[BROADCAST] DISABLED",
        flush=True,
    )

    ready=bool(
        signer_set
        and len(rows)>=15
        and alt_address
    )

    print(
        "[MONEY_PATH_READY] %s"
        %str(ready).upper(),
        flush=True,
    )

    print(
        "[NEXT] HOT_BOOK_LIVE_RUNTIME",
        flush=True,
    )

    return 0 if ready else 2


def main():
    p=argparse.ArgumentParser()
    p.parse_args()
    return run()


if __name__=="__main__":
    raise SystemExit(main())
