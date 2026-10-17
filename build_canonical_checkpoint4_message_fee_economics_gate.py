from pathlib import Path

ROOT=Path.cwd()
PKG=ROOT/"qseries_v2"/"oracle_execution"/"solana_atomic_executor"
TARGET=PKG/"checkpoint4_message_fee_economics_gate.py"
TEST=ROOT/"test_canonical_checkpoint4_message_fee_economics_gate.py"

MODULE=r'''from __future__ import annotations

import base64
from qseries_v2.oracle_execution.solana_atomic_executor import runtime as r
from qseries_v2.oracle_execution.solana_atomic_executor import checkpoint2_forward_atomic_sim as cp
from qseries_v2.oracle_execution.solana_atomic_executor import checkpoint3_reverse_atomic_compile as c3


class _Checkpoint4Complete(Exception):
    pass


def _message_fee_lamports(compiled):
    msg=compiled.get("msg")
    if msg is None:
        raise RuntimeError("CHECKPOINT4_MESSAGE_MISSING")

    encoded=base64.b64encode(bytes(msg)).decode()

    result=r.q87.c.rpc(
        "getFeeForMessage",
        [
            encoded,
            {
                "commitment":"processed",
            },
        ],
    )

    if not isinstance(result,dict):
        raise RuntimeError("CHECKPOINT4_FEE_RESULT_NOT_MAPPING")

    value=result.get("value")

    if value is None:
        raise RuntimeError("CHECKPOINT4_FEE_UNAVAILABLE")

    fee=int(value)

    if fee < 0:
        raise RuntimeError("CHECKPOINT4_NEGATIVE_FEE")

    return fee


def evaluate(user,snap):
    reverse=c3._reverse_opportunity(snap)
    route=c3._reverse_route(user,snap,reverse)

    compiled=r.compile_current(
        user,
        route,
    )

    if not compiled.get("ok"):
        print(
            "[CHECKPOINT4_COMPILE_FAIL] %s"%compiled,
            flush=True,
        )
        return {
            "ok":False,
            "phase":"compile",
            "compiled":compiled,
        }

    fee=_message_fee_lamports(compiled)

    gross=int(reverse["local_net"])
    after=gross-fee
    start=int(reverse["start"])
    after_bps=(
        after/start*10000.0
        if start>0
        else 0.0
    )

    print(
        "[CHECKPOINT4_MESSAGE_FEE] "
        "lamports=%d"%fee,
        flush=True,
    )
    print(
        "[CHECKPOINT4_ECONOMICS] "
        "direction=METEORA_TO_PUMP "
        "gross_net=%+d "
        "message_fee=%d "
        "after_message_fee=%+d "
        "after_message_fee_bps=%+.2f"
        %(
            gross,
            fee,
            after,
            after_bps,
        ),
        flush=True,
    )

    admitted=after>0

    print(
        "[CHECKPOINT4_GATE] "
        "status=%s"
        %(
            "PASS_POSITIVE_AFTER_MESSAGE_FEE"
            if admitted
            else "HOLD_NONPOSITIVE_AFTER_MESSAGE_FEE"
        ),
        flush=True,
    )

    print(
        "[CHECKPOINT4_SCOPE] "
        "message_fee_only=True "
        "priority_fee_and_simulation_pending=True",
        flush=True,
    )
    print("[BROADCAST] disabled",flush=True)

    return {
        "ok":True,
        "direction":"METEORA_TO_PUMP",
        "bytes":int(compiled.get("bytes") or 0),
        "gross_net_lamports":gross,
        "message_fee_lamports":fee,
        "after_message_fee_lamports":after,
        "after_message_fee_bps":after_bps,
        "admitted":admitted,
        "simulation":False,
        "broadcast":False,
    }


def main():
    captured={}
    original=r._execute_route_once

    def intercept(user,snap,_forward):
        captured["result"]=evaluate(user,snap)
        raise _Checkpoint4Complete()

    r._execute_route_once=intercept

    try:
        try:
            cp.main()
        except _Checkpoint4Complete:
            pass
    finally:
        r._execute_route_once=original

    result=captured.get("result")

    if not isinstance(result,dict):
        raise RuntimeError(
            "CHECKPOINT4_ROUTE_NOT_MATERIALIZED"
        )

    if not result.get("ok"):
        return 1

    print(
        "[CHECKPOINT4_FINAL] "
        "status=PASS_MEASUREMENT "
        "admitted=%s"
        %str(bool(result.get("admitted"))),
        flush=True,
    )

    return 0


if __name__=="__main__":
    raise SystemExit(main())
'''

TEST_CODE='''import ast
import unittest
from pathlib import Path

P=Path(
 "qseries_v2/oracle_execution/solana_atomic_executor/"
 "checkpoint4_message_fee_economics_gate.py"
)

class T(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.s=P.read_text(encoding="utf-8")
        ast.parse(cls.s)

    def test_real_fee_rpc(self):
        self.assertIn('"getFeeForMessage"',self.s)

    def test_fee_subtracted(self):
        self.assertIn("after=gross-fee",self.s)

    def test_positive_only_gate(self):
        self.assertIn("admitted=after>0",self.s)
        self.assertIn("HOLD_NONPOSITIVE_AFTER_MESSAGE_FEE",self.s)

    def test_scope_is_honest(self):
        self.assertIn(
            "priority_fee_and_simulation_pending=True",
            self.s,
        )

    def test_no_simulation(self):
        self.assertNotIn("simulateTransaction",self.s)

    def test_no_broadcast(self):
        self.assertNotIn("sendTransaction",self.s)
        self.assertNotIn(".send(",self.s)

    def test_reuses_clean_reverse_path(self):
        self.assertIn("c3._reverse_opportunity(",self.s)
        self.assertIn("c3._reverse_route(",self.s)

if __name__=="__main__":
    unittest.main(verbosity=2)
'''

TARGET.write_text(MODULE,encoding="utf-8")
TEST.write_text(TEST_CODE,encoding="utf-8")

print("[PASS] canonical checkpoint-4 message-fee economics gate installed")
print("[INPUT] certified checkpoint-3 reverse route")
print("[FEE] real getFeeForMessage RPC")
print("[GATE] positive after message fee only")
print("[SCOPE] priority fee + funded simulation remain pending")
print("[ALT] unchanged")
print("[KEY] untouched")
print("[BROADCAST] disabled")
print("[TEST]",TEST.name)
