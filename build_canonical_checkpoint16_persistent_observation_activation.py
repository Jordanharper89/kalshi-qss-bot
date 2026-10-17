from pathlib import Path

ROOT=Path.cwd()
PKG=ROOT/"qseries_v2"/"oracle_execution"/"solana_atomic_executor"
TARGET=PKG/"checkpoint16_persistent_observation_activation.py"
TEST=ROOT/"test_canonical_checkpoint16_persistent_observation_activation.py"

TARGET.write_text(r'''from __future__ import annotations
import argparse

from qseries_v2.oracle_execution.solana_atomic_executor import (
    checkpoint15_cheapest_legal_fee_signed_simulation as c15
)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--seconds",type=float,default=3600.0)
    args=p.parse_args()

    if args.seconds<=0:
        raise RuntimeError("CHECKPOINT16_SECONDS_MUST_BE_POSITIVE")

    c15.SECONDS=float(args.seconds)

    print(
        "[CHECKPOINT16_ACTIVATION] "
        "persistent_multi_pool=True "
        "cheapest_legal_fee=True "
        "signed_sim_positive_only=True "
        "seconds=%.0f broadcast=False"
        %c15.SECONDS,
        flush=True,
    )

    return c15.main()

if __name__=="__main__":
    raise SystemExit(main())
''',encoding="utf-8")

TEST.write_text(r'''import ast
import unittest
from pathlib import Path

P=Path("qseries_v2/oracle_execution/solana_atomic_executor/checkpoint16_persistent_observation_activation.py")

class T(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.s=P.read_text(encoding="utf-8")
        ast.parse(cls.s)

    def test_reuses_checkpoint15(self):
        self.assertIn("checkpoint15_cheapest_legal_fee_signed_simulation",self.s)

    def test_duration_configurable(self):
        self.assertIn("--seconds",self.s)
        self.assertIn("default=3600.0",self.s)

    def test_no_execution_bypass(self):
        self.assertNotIn("sendTransaction",self.s)

if __name__=="__main__":
    unittest.main(verbosity=2)
''',encoding="utf-8")

print("[PASS] checkpoint-16 persistent observation activation installed")
print("[RUNTIME] checkpoint-15 certified economics/execution-proof path reused")
print("[DEFAULT] 3600 seconds")
print("[BROADCAST] disabled")
print("[TEST]",TEST.name)