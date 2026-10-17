from pathlib import Path

ROOT=Path.cwd()
TARGET=ROOT/"qseries_v2"/"oracle_execution"/"solana_atomic_executor"/"checkpoint3_reverse_atomic_compile.py"
TEST=ROOT/"test_canonical_checkpoint3_clean_replacement.py"

if not TARGET.is_file():
    raise SystemExit("checkpoint3_reverse_atomic_compile.py missing")

src=TARGET.read_text(encoding="utf-8")

start=src.find("\ndef main():")
if start < 0:
    raise SystemExit("checkpoint3 main() marker missing")

prefix=src[:start]

new_tail=r"""

class _Checkpoint3Complete(Exception):
    pass


def main():
    captured={}
    original=r._execute_route_once

    def checkpoint3_intercept(user,snap,_forward):
        captured["result"]=compile_reverse(user,snap)
        raise _Checkpoint3Complete()

    r._execute_route_once=checkpoint3_intercept

    try:
        try:
            cp.main()
        except _Checkpoint3Complete:
            pass
    finally:
        r._execute_route_once=original

    result=captured.get("result")

    if not isinstance(result,dict):
        raise RuntimeError(
            "CHECKPOINT3_REVERSE_ROUTE_NOT_MATERIALIZED"
        )

    if not result.get("ok"):
        print(
            "[CHECKPOINT3_REVERSE_FINAL] status=FAIL",
            flush=True,
        )
        return 1

    print(
        "[CHECKPOINT3_REVERSE_FINAL] "
        "status=PASS bytes=%d"
        %int(result.get("bytes") or 0),
        flush=True,
    )
    print(
        "[CHECKPOINT3_HARNESS] "
        "checkpoint2_bootstrap_only=True "
        "simulation_fallthrough=False",
        flush=True,
    )
    print("[BROADCAST] disabled",flush=True)
    return 0


if __name__=="__main__":
    raise SystemExit(main())
"""

TARGET.write_text(prefix+new_tail,encoding="utf-8")

test_code = '''import ast
import unittest
from pathlib import Path

P=Path(
 "qseries_v2/oracle_execution/solana_atomic_executor/"
 "checkpoint3_reverse_atomic_compile.py"
)

class T(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.s=P.read_text(encoding="utf-8")
        ast.parse(cls.s)

    def test_single_clean_main(self):
        self.assertEqual(self.s.count("def main():"),1)

    def test_control_flow_sentinel(self):
        self.assertIn("class _Checkpoint3Complete(Exception):",self.s)
        self.assertIn("raise _Checkpoint3Complete()",self.s)

    def test_no_sim_contract_dependency(self):
        tail=self.s[self.s.index("def main():"):]
        self.assertNotIn('result["sim"]',tail)
        self.assertNotIn("simulate_current(",tail)

    def test_reverse_certification_preserved(self):
        self.assertIn("CHECKPOINT3_REVERSE_COMPILE_PASS",self.s)
        self.assertIn("METEORA_TO_PUMP",self.s)
        self.assertIn("_build_meteora_reverse_ix_hot(",self.s)

    def test_no_broadcast(self):
        self.assertNotIn("sendTransaction",self.s)

if __name__=="__main__":
    unittest.main(verbosity=2)
'''

TEST.write_text(test_code,encoding="utf-8")

print("[PASS] checkpoint-3 clean replacement installed")
print("[PRESERVED] certified reverse builder + canonical compile")
print("[REMOVED] checkpoint-2 simulation fall-through")
print("[DEPENDENCY] checkpoint-2 bootstrap only")
print("[ALT] unchanged")
print("[KEY] untouched")
print("[BROADCAST] disabled")
print("[TEST]",TEST.name)
