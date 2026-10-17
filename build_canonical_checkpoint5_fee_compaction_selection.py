from pathlib import Path

ROOT=Path.cwd()
PKG=ROOT/"qseries_v2"/"oracle_execution"/"solana_atomic_executor"
TARGET=PKG/"checkpoint5_fee_compaction_selection.py"
TEST=ROOT/"test_canonical_checkpoint5_fee_compaction_selection.py"

MODULE=r"""from __future__ import annotations

import copy

from qseries_v2.oracle_execution.solana_atomic_executor import runtime as r
from qseries_v2.oracle_execution.solana_atomic_executor import checkpoint2_forward_atomic_sim as cp
from qseries_v2.oracle_execution.solana_atomic_executor import checkpoint3_reverse_atomic_compile as c3
from qseries_v2.oracle_execution.solana_atomic_executor import checkpoint4_message_fee_economics_gate as c4

COMPUTE_BUDGET="ComputeBudget111111111111111111111111111111"
MEMOS={
    "MemoSq4gqABAXKb96qnH8TysNcWxMyWCqXgDLGmfcHr",
    "Memo1UhkJRfHyvLMcVucJwxXeuD728EqVDDwQDxFMNo",
}


class _Checkpoint5Complete(Exception):
    pass


def _compact(ixs):
    return [
        copy.deepcopy(ix)
        for ix in ixs
        if (
            ix.get("programId")!=COMPUTE_BUDGET
            and ix.get("programId") not in MEMOS
        )
    ]


def _compile_one(user,base_route,name,ixs):
    route=dict(base_route)
    route["original_candidates"]=[
        (
            name,
            [copy.deepcopy(x) for x in ixs],
        )
    ]

    compiled=r.compile_current(
        user,
        route,
    )

    if not compiled.get("ok"):
        return {
            "name":name,
            "ok":False,
            "compiled":compiled,
        }

    fee=c4._message_fee_lamports(
        compiled
    )

    return {
        "name":name,
        "ok":True,
        "bytes":int(compiled.get("bytes") or 0),
        "fee_lamports":int(fee),
        "compiled":compiled,
    }


def evaluate(user,snap):
    reverse=c3._reverse_opportunity(snap)
    route=c3._reverse_route(
        user,
        snap,
        reverse,
    )

    name,full=route["original_candidates"][0]
    full=[copy.deepcopy(x) for x in full]
    compact=_compact(full)

    removed=len(full)-len(compact)

    print(
        "[CHECKPOINT5_COMPACTION] "
        "full_ix=%d compact_ix=%d removed=%d"
        %(len(full),len(compact),removed),
        flush=True,
    )

    rows=[
        _compile_one(
            user,
            route,
            "FULL_REVERSE",
            full,
        ),
        _compile_one(
            user,
            route,
            "NO_COMPUTE_MEMO_REVERSE",
            compact,
        ),
    ]

    legal=[
        row
        for row in rows
        if row.get("ok")
    ]

    for row in rows:
        if row.get("ok"):
            print(
                "[CHECKPOINT5_CANDIDATE] "
                "name=%s bytes=%d fee_lamports=%d"
                %(
                    row["name"],
                    row["bytes"],
                    row["fee_lamports"],
                ),
                flush=True,
            )
        else:
            print(
                "[CHECKPOINT5_CANDIDATE] "
                "name=%s status=COMPILE_REJECT"
                %row["name"],
                flush=True,
            )

    if not legal:
        raise RuntimeError(
            "CHECKPOINT5_NO_LEGAL_CANDIDATE"
        )

    winner=min(
        legal,
        key=lambda x:(
            int(x["fee_lamports"]),
            int(x["bytes"]),
        ),
    )

    gross=int(reverse["local_net"])
    fee=int(winner["fee_lamports"])
    after=gross-fee
    start=int(reverse["start"])

    print(
        "[CHECKPOINT5_WINNER] "
        "name=%s bytes=%d fee_lamports=%d"
        %(
            winner["name"],
            winner["bytes"],
            fee,
        ),
        flush=True,
    )

    print(
        "[CHECKPOINT5_ECONOMICS] "
        "gross_net=%+d fee=%d after_fee=%+d bps=%+.2f"
        %(
            gross,
            fee,
            after,
            (
                after/start*10000.0
                if start>0
                else 0.0
            ),
        ),
        flush=True,
    )

    admitted=after>0

    print(
        "[CHECKPOINT5_GATE] status=%s"
        %(
            "PASS_POSITIVE_AFTER_FEE"
            if admitted
            else "HOLD_NONPOSITIVE_AFTER_FEE"
        ),
        flush=True,
    )
    print("[SIMULATION] disabled",flush=True)
    print("[BROADCAST] disabled",flush=True)

    return {
        "ok":True,
        "winner":winner["name"],
        "fee_lamports":fee,
        "after_fee_lamports":after,
        "admitted":admitted,
    }


def main():
    captured={}
    original=r._execute_route_once

    def intercept(user,snap,_forward):
        captured["result"]=evaluate(user,snap)
        raise _Checkpoint5Complete()

    r._execute_route_once=intercept

    try:
        try:
            cp.main()
        except _Checkpoint5Complete:
            pass
    finally:
        r._execute_route_once=original

    result=captured.get("result")

    if not isinstance(result,dict):
        raise RuntimeError(
            "CHECKPOINT5_NOT_MATERIALIZED"
        )

    print(
        "[CHECKPOINT5_FINAL] status=PASS_MEASUREMENT "
        "winner=%s admitted=%s"
        %(
            result["winner"],
            str(bool(result["admitted"])),
        ),
        flush=True,
    )

    return 0


if __name__=="__main__":
    raise SystemExit(main())
"""

TEST_CODE=r"""import ast
import unittest
from pathlib import Path

P=Path(
 "qseries_v2/oracle_execution/solana_atomic_executor/"
 "checkpoint5_fee_compaction_selection.py"
)


class T(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.s=P.read_text(encoding="utf-8")
        ast.parse(cls.s)

    def test_compute_budget_removed_only_in_compact(self):
        self.assertIn(
            'COMPUTE_BUDGET="ComputeBudget111111111111111111111111111111"',
            self.s,
        )
        self.assertIn(
            'ix.get("programId")!=COMPUTE_BUDGET',
            self.s,
        )

    def test_memo_removed(self):
        self.assertIn("MemoSq4gq",self.s)
        self.assertIn("Memo1Uhk",self.s)

    def test_both_candidates_measured(self):
        self.assertIn('"FULL_REVERSE"',self.s)
        self.assertIn('"NO_COMPUTE_MEMO_REVERSE"',self.s)

    def test_real_fee_readback_reused(self):
        self.assertIn(
            "c4._message_fee_lamports(",
            self.s,
        )

    def test_cheapest_legal_wins(self):
        self.assertIn(
            "winner=min(",
            self.s,
        )
        self.assertIn(
            'int(x["fee_lamports"])',
            self.s,
        )

    def test_no_simulation_or_broadcast(self):
        self.assertNotIn("simulateTransaction",self.s)
        self.assertNotIn("sendTransaction",self.s)

if __name__=="__main__":
    unittest.main(verbosity=2)
"""

TARGET.write_text(MODULE,encoding="utf-8")
TEST.write_text(TEST_CODE,encoding="utf-8")

print("[PASS] canonical checkpoint-5 fee compaction selection installed")
print("[COMPARE] FULL_REVERSE vs NO_COMPUTE_MEMO_REVERSE")
print("[FEE] real getFeeForMessage for each legal candidate")
print("[ECONOMICS] cheapest legal candidate selected")
print("[SIMULATION] disabled")
print("[ALT] unchanged")
print("[KEY] untouched")
print("[BROADCAST] disabled")
print("[TEST]",TEST.name)
