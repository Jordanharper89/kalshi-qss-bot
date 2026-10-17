from pathlib import Path

ROOT=Path.cwd()
PKG=ROOT/"qseries_v2"/"oracle_execution"/"solana_atomic_executor"
TARGET=PKG/"checkpoint20_canonical_alt_bidirectional_compile.py"
TEST=ROOT/"test_canonical_checkpoint20_canonical_alt_bidirectional_compile.py"

MODULE=r"""from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from qseries_v2.oracle_execution.solana_atomic_executor import runtime as r
from qseries_v2.oracle_execution.solana_atomic_executor import checkpoint13_live_reverse_fee_execution_proof as c13
from qseries_v2.oracle_execution.solana_atomic_executor import checkpoint15_cheapest_legal_fee_signed_simulation as c15
from qseries_v2.oracle_execution.solana_atomic_executor import checkpoint19_bidirectional_best_first_signed_simulation as c19

ALT_STATE=Path(
    "runtime_state/oracle/solana_atomic_executor/"
    "canonical_alt.json"
)


def _load_canonical_alt():
    path=Path.cwd()/ALT_STATE

    if not path.is_file():
        raise RuntimeError(
            "CHECKPOINT20_CANONICAL_ALT_STATE_MISSING:"
            +str(path)
        )

    payload=json.loads(
        path.read_text(encoding="utf-8")
    )

    address=None

    if isinstance(payload,dict):
        for key in (
            "address",
            "canonical_alt",
            "alt_address",
            "lookup_table",
            "table",
        ):
            value=payload.get(key)

            if isinstance(value,str) and value:
                address=value
                break

    if not address:
        raise RuntimeError(
            "CHECKPOINT20_CANONICAL_ALT_ADDRESS_MISSING"
        )

    return address


def _compile_all_legal_with_alt(
    user,
    route,
    gross,
):
    blockhash=r.BLOCKHASH.get()
    canonical_alt=_load_canonical_alt()
    rows=[]

    for candidate in list(
        r.q87.repaired_candidates(route)
    ):
        name=str(
            candidate.get(
                "name",
                "UNKNOWN",
            )
        )

        if "PUMP_METEORA_ONLY" in name:
            continue

        comp=r.q87.compile_candidate(
            user,
            candidate["instructions"],
            [[canonical_alt]],
            blockhash,
        )

        if (
            not isinstance(comp,dict)
            or not comp.get("ok")
        ):
            print(
                "[CHECKPOINT20_COMPILE_HOLD] "
                "candidate=%s error=%s attempts=%s"
                %(
                    name,
                    str(
                        comp.get("error")
                        if isinstance(comp,dict)
                        else "NON_MAPPING_COMPILE"
                    ),
                    str(
                        comp.get("attempts")
                        if isinstance(comp,dict)
                        else None
                    )[:280],
                ),
                flush=True,
            )
            continue

        raw=comp["unsigned"]
        size=len(raw)

        print(
            "[CHECKPOINT20_COMPILED] "
            "candidate=%s bytes=%d alt=%s"
            %(
                name,
                size,
                canonical_alt[:12],
            ),
            flush=True,
        )

        if size>r.MAX_TX_BYTES:
            print(
                "[CHECKPOINT20_SIZE_HOLD] "
                "candidate=%s bytes=%d max=%d"
                %(
                    name,
                    size,
                    r.MAX_TX_BYTES,
                ),
                flush=True,
            )
            continue

        c15.WATCH[
            "candidate_compiles"
        ]+=1

        compiled={
            "ok":True,
            "candidate":name,
            "bytes":size,
            "msg":comp["msg"],
            "raw":raw,
            "canonical_alt":canonical_alt,
        }

        try:
            fee=c13._fee_for_message(
                compiled
            )
        except Exception as exc:
            print(
                "[CHECKPOINT20_FEE_ERROR] "
                "candidate=%s %s:%s"
                %(
                    name,
                    type(exc).__name__,
                    str(exc)[:220],
                ),
                flush=True,
            )
            continue

        c15.WATCH[
            "candidate_fees"
        ]+=1

        after_fee=(
            int(gross)
            -int(fee)
        )

        print(
            "[CHECKPOINT20_CANDIDATE] "
            "candidate=%s bytes=%d fee=%d "
            "gross=%+d after_fee=%+d"
            %(
                name,
                size,
                int(fee),
                int(gross),
                after_fee,
            ),
            flush=True,
        )

        rows.append({
            "compiled":compiled,
            "fee":int(fee),
            "after_fee":after_fee,
        })

    if not rows:
        return None

    return max(
        rows,
        key=lambda x:int(
            x["after_fee"]
        ),
    )


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
            "CHECKPOINT20_SECONDS_MUST_BE_POSITIVE"
        )

    canonical_alt=_load_canonical_alt()

    old_compile=c15._compile_all_legal
    old_argv=list(sys.argv)

    try:
        c15._compile_all_legal=(
            _compile_all_legal_with_alt
        )

        print(
            "[CHECKPOINT20_ACTIVATION] "
            "canonical_alt_compile=True "
            "bidirectional=True "
            "seconds=%.0f broadcast=False"
            %args.seconds,
            flush=True,
        )

        print(
            "[CHECKPOINT20_ALT] "
            "persisted=True address=%s"
            %canonical_alt,
            flush=True,
        )

        print(
            "[CHECKPOINT20_PIPELINE] "
            "both_directions -> full_ladder -> "
            "best_first -> pair_key_route -> "
            "canonical_alt_compile -> real_fee -> "
            "signed_simulation",
            flush=True,
        )

        print(
            "[BROADCAST] disabled",
            flush=True,
        )

        sys.argv=[
            old_argv[0],
            "--seconds",
            str(float(args.seconds)),
        ]

        return c19.main()

    finally:
        c15._compile_all_legal=old_compile
        sys.argv=old_argv


if __name__=="__main__":
    raise SystemExit(main())
"""

TEST_CODE=r"""import ast
import unittest
from pathlib import Path

P=Path(
 "qseries_v2/oracle_execution/solana_atomic_executor/"
 "checkpoint20_canonical_alt_bidirectional_compile.py"
)


class T(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.s=P.read_text(encoding="utf-8")
        ast.parse(cls.s)

    def test_canonical_alt_required(self):
        self.assertIn(
            "canonical_alt.json",
            self.s,
        )
        self.assertIn(
            "_load_canonical_alt()",
            self.s,
        )

    def test_compile_uses_alt(self):
        self.assertIn(
            "[[canonical_alt]]",
            self.s,
        )
        self.assertNotIn(
            "candidate[\"instructions\"],\n            [[]],",
            self.s,
        )

    def test_compile_fail_visible(self):
        self.assertIn(
            "[CHECKPOINT20_COMPILE_HOLD]",
            self.s,
        )
        self.assertIn(
            'comp.get("error")',
            self.s,
        )

    def test_real_fee_preserved(self):
        self.assertIn(
            "c13._fee_for_message(",
            self.s,
        )

    def test_checkpoint19_reused(self):
        self.assertIn(
            "return c19.main()",
            self.s,
        )

    def test_no_broadcast(self):
        self.assertNotIn(
            "sendTransaction",
            self.s,
        )


if __name__=="__main__":
    unittest.main(verbosity=2)
"""

TARGET.write_text(
    MODULE,
    encoding="utf-8",
)

TEST.write_text(
    TEST_CODE,
    encoding="utf-8",
)

print("[PASS] checkpoint-20 canonical-ALT bidirectional compile installed")
print("[FIX] checkpoint-15 empty ALT compile replaced by persisted canonical ALT")
print("[DIRECTIONS] forward + reverse preserved through checkpoint-19")
print("[RANK] full size ladder best-first preserved")
print("[FEE] real getFeeForMessage preserved")
print("[SIMULATION] signed best-after-fee candidate preserved")
print("[ALT] existing canonical ALT only; no creation or extension")
print("[KEY] existing signer read only; untouched")
print("[BROADCAST] disabled")
print("[TEST]",TEST.name)
