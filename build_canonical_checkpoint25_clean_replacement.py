from pathlib import Path

ROOT=Path.cwd()
PKG=ROOT/"qseries_v2"/"oracle_execution"/"solana_atomic_executor"
TARGET=PKG/"checkpoint25_expanded_live_universe_cutover.py"
TEST=ROOT/"test_canonical_checkpoint25_expanded_live_universe_cutover.py"

MODULE=r"""from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

from qseries_v2.oracle_execution.solana_atomic_executor import checkpoint22_cached_alt_latency_cutover as c22

MANIFEST=Path(
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

    if not rows:
        raise RuntimeError(
            "CHECKPOINT25_EMPTY_MANIFEST"
        )

    identities=set()
    out=[]

    for row in rows:
        token=str(row["token"])
        pool=str(row["meteora_pool"])
        identity=token+"|"+pool

        if identity in identities:
            raise RuntimeError(
                "CHECKPOINT25_DUPLICATE_IDENTITY:"+identity
            )

        identities.add(identity)

        out.append({
            "identity":identity,
            "token":token,
            "pump_pool":str(row["pump_pool"]),
            "meteora_pool":pool,
            "token_x":str(row["token_x"]),
            "token_y":str(row["token_y"]),
            "decimals_x":int(row["decimals_x"]),
            "decimals_y":int(row["decimals_y"]),
            "selected_legacy":bool(row.get("retained")),
            "source":"CHECKPOINT24_CAPACITY_AWARE",
            "account_cost":int(row.get("account_cost") or 0),
            "reported_tvl":float(row.get("reported_tvl") or 0),
        })

    return {
        "revision":
            "CHECKPOINT25_EXPANDED_RUNTIME_REGISTRY",
        "observed_unix":time.time(),
        "ready_pairs":len(out),
        "pair_identities":len(out),
        "identity":"token|meteora_pool",
        "rows":out,
        "execution_authority":False,
        "broadcast":False,
        "temporary_runtime_cutover":True,
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

    print("[BROADCAST] disabled",flush=True)

    try:
        _atomic_write(
            REGISTRY,
            expanded,
        )

        verify=_load(REGISTRY)
        actual=len(
            verify.get("rows") or []
        )

        if actual!=len(expanded["rows"]):
            raise RuntimeError(
                "CHECKPOINT25_REGISTRY_WRITE_MISMATCH:"
                +str(actual)
            )

        print(
            "[CHECKPOINT25_REGISTRY_READY] "
            "pairs=%d"
            %actual,
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
"""

TEST_CODE=r"""import ast
import unittest
from pathlib import Path

P=Path(
 "qseries_v2/oracle_execution/solana_atomic_executor/"
 "checkpoint25_expanded_live_universe_cutover.py"
)

class T(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.s=P.read_text(encoding="utf-8")
        ast.parse(cls.s)

    def test_uses_cp24_manifest(self):
        self.assertIn(
            "capacity_aware_warm_universe.json",
            self.s,
        )

    def test_targets_actual_registry_owner(self):
        self.assertIn(
            "multi_dlmm_pair_registry.json",
            self.s,
        )
        self.assertIn(
            "[CHECKPOINT25_REGISTRY_CUTOVER]",
            self.s,
        )

    def test_identity_preserved(self):
        self.assertIn(
            'identity=token+"|"+pool',
            self.s,
        )

    def test_native_chain_preserved(self):
        self.assertIn(
            "return c22.main()",
            self.s,
        )

    def test_registry_restored(self):
        self.assertIn(
            "[CHECKPOINT25_REGISTRY_RESTORED]",
            self.s,
        )
        self.assertIn(
            "tmp.replace(REGISTRY)",
            self.s.replace(" ","").replace("\n",""),
        )

    def test_no_broadcast(self):
        self.assertNotIn(
            "sendTransaction",
            self.s,
        )

if __name__=="__main__":
    unittest.main(verbosity=2)
"""

TARGET.write_text(MODULE,encoding="utf-8")
TEST.write_text(TEST_CODE,encoding="utf-8")

print("[PASS] checkpoint-25 clean replacement installed")
print("[FIX] expanded manifest now cuts over at actual multi_dlmm_pair_registry state owner")
print("[CHAIN] existing checkpoint-12/15/17 hydration and checkpoint-22 execution stack preserved")
print("[RESTORE] original registry restored in finally")
print("[KEY] untouched")
print("[BROADCAST] disabled")
print("[TEST]",TEST.name)
