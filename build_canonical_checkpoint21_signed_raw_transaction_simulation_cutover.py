from pathlib import Path

ROOT=Path.cwd()
PKG=ROOT/"qseries_v2"/"oracle_execution"/"solana_atomic_executor"
TARGET=PKG/"checkpoint21_signed_raw_transaction_simulation_cutover.py"
TEST=ROOT/"test_canonical_checkpoint21_signed_raw_transaction_simulation_cutover.py"

MODULE=r"""from __future__ import annotations

import argparse
import base64
import sys
import time
import urllib.error

from qseries_v2.oracle_execution.solana_atomic_executor import runtime as r
from qseries_v2.oracle_execution.solana_atomic_executor import checkpoint14_fee_positive_signed_simulation as c14
from qseries_v2.oracle_execution.solana_atomic_executor import checkpoint20_canonical_alt_bidirectional_compile as c20


def _signed_simulation_raw(compiled):
    if c14.SIGNER is None:
        raise RuntimeError("CHECKPOINT21_SIGNER_UNAVAILABLE")

    msg=compiled.get("msg")
    if not isinstance(msg,(bytes,bytearray)):
        raise RuntimeError(
            "CHECKPOINT21_MESSAGE_NOT_BYTES:"+type(msg).__name__
        )

    raw=r.q87.c.signed_tx(bytes(msg),c14.SIGNER)
    encoded=base64.b64encode(raw).decode()
    last=None

    for attempt in range(1,7):
        try:
            result=r.q87.c.rpc(
                "simulateTransaction",
                [
                    encoded,
                    {
                        "encoding":"base64",
                        "sigVerify":True,
                        "replaceRecentBlockhash":False,
                        "commitment":"processed",
                    },
                ],
            )

            if not isinstance(result,dict):
                raise RuntimeError(
                    "CHECKPOINT21_SIM_RESULT_NOT_MAPPING:"+type(result).__name__
                )

            value=result.get("value")
            if not isinstance(value,dict):
                raise RuntimeError(
                    "CHECKPOINT21_SIM_VALUE_NOT_MAPPING:"+type(value).__name__
                )

            return {
                "err":value.get("err"),
                "units":value.get("unitsConsumed"),
                "logs":value.get("logs") or [],
                "signed_bytes":len(raw),
            }

        except urllib.error.HTTPError as exc:
            last=exc
            if getattr(exc,"code",None)!=429 or attempt>=6:
                raise
            delay=min(0.5*(2**(attempt-1)),4.0)
            print(
                "[CHECKPOINT21_SIM_429_RETRY] attempt=%d sleep=%.2fs"%(attempt,delay),
                flush=True,
            )
            time.sleep(delay)

    raise last if last else RuntimeError("CHECKPOINT21_SIMULATION_FAILED")


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--seconds",type=float,default=3600.0)
    args=p.parse_args()

    if args.seconds<=0:
        raise RuntimeError("CHECKPOINT21_SECONDS_MUST_BE_POSITIVE")

    old_sim=c14._signed_simulation
    old_argv=list(sys.argv)

    try:
        c14._signed_simulation=_signed_simulation_raw

        print(
            "[CHECKPOINT21_ACTIVATION] signed_raw_tx_simulation=True seconds=%.0f broadcast=False"%args.seconds,
            flush=True,
        )
        print(
            "[CHECKPOINT21_SIGNING] message_bytes -> existing signer -> signed raw transaction -> simulateTransaction(sigVerify=True)",
            flush=True,
        )
        print(
            "[CHECKPOINT21_PIPELINE] checkpoint20 canonical_ALT compile -> real_fee -> best_after_fee -> freshness -> signed_raw_simulation",
            flush=True,
        )
        print("[BROADCAST] disabled",flush=True)

        sys.argv=[old_argv[0],"--seconds",str(float(args.seconds))]
        return c20.main()

    finally:
        c14._signed_simulation=old_sim
        sys.argv=old_argv


if __name__=="__main__":
    raise SystemExit(main())
"""

TEST_CODE=r"""import ast
import unittest
from pathlib import Path

P=Path("qseries_v2/oracle_execution/solana_atomic_executor/checkpoint21_signed_raw_transaction_simulation_cutover.py")

class T(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.s=P.read_text(encoding="utf-8")
        ast.parse(cls.s)

    def test_uses_existing_signed_tx_helper(self):
        self.assertIn("r.q87.c.signed_tx(",self.s)

    def test_requires_message_bytes(self):
        self.assertIn("(bytes,bytearray)",self.s)

    def test_sigverify_true(self):
        self.assertIn('"sigVerify":True',self.s)

    def test_no_versionedtransaction_constructor(self):
        self.assertNotIn("VersionedTransaction(",self.s)

    def test_checkpoint20_reused(self):
        self.assertIn("return c20.main()",self.s)

    def test_no_broadcast(self):
        self.assertNotIn("sendTransaction",self.s)

if __name__=="__main__":
    unittest.main(verbosity=2)
"""

TARGET.write_text(MODULE,encoding="utf-8")
TEST.write_text(TEST_CODE,encoding="utf-8")

print("[PASS] checkpoint-21 signed raw transaction simulation cutover installed")
print("[FIX] raw v0 message bytes signed with existing canonical signer helper")
print("[SIMULATION] signed raw transaction + sigVerify=True")
print("[COMPILE] checkpoint-20 canonical ALT path preserved")
print("[FEE] real message-fee gate preserved")
print("[FRESHNESS] checkpoint-19 generation/age gates preserved")
print("[KEY] existing signer read only; untouched")
print("[BROADCAST] disabled")
print("[TEST]",TEST.name)
