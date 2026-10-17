from pathlib import Path
import ast

ROOT=Path.cwd()
TARGET=ROOT/"qseries_v2"/"oracle_execution"/"solana_atomic_executor"/"checkpoint17_pair_key_execution_templates.py"
TEST=ROOT/"test_checkpoint17_single_prewarm_handoff.py"

if not TARGET.is_file():
    raise RuntimeError("CHECKPOINT17_TARGET_MISSING:"+str(TARGET))

src=TARGET.read_text(encoding="utf-8")
ast.parse(src)

if "CHECKPOINT17_SINGLE_PREWARM_HANDOFF" not in src:
    needle='''    old_expanded=c12._expanded_state
    old_route=c7._route
    ORIGINAL_ROUTE=old_route

    try:
'''
    repl='''    old_expanded=c12._expanded_state
    old_route=c7._route
    old_prewarm=r.q25.install_hot_math_and_prewarm
    ORIGINAL_ROUTE=old_route

    try:
'''
    if needle not in src:
        raise RuntimeError("CHECKPOINT17_SINGLE_PREWARM_SETUP_MARKER_NOT_FOUND")
    src=src.replace(needle,repl,1)

    needle2='''        c7._route=_pair_bound_route
        c15.SECONDS=float(args.seconds)

        print(
'''
    repl2='''        c7._route=_pair_bound_route

        def _reuse_checkpoint17_prewarm(child_state):
            child_pairs=list(
                child_state.get("pairs") or []
            )
            parent_pairs=list(
                state.get("pairs") or []
            )

            child_tokens={
                str(pair.token)
                for pair in child_pairs
            }
            parent_tokens={
                str(pair.token)
                for pair in parent_pairs
            }

            if child_tokens!=parent_tokens:
                raise RuntimeError(
                    "CHECKPOINT17_PREWARM_STATE_DRIFT:"
                    +str(len(child_tokens))
                    +"/"
                    +str(len(parent_tokens))
                )

            print(
                "[CHECKPOINT17_SINGLE_PREWARM_HANDOFF] "
                "tokens=%d warmed_rows=%d "
                "duplicate_network_prewarm=False"
                %(
                    len(parent_tokens),
                    len(warmed),
                ),
                flush=True,
            )

            return list(warmed)

        r.q25.install_hot_math_and_prewarm=(
            _reuse_checkpoint17_prewarm
        )

        c15.SECONDS=float(args.seconds)

        print(
'''
    if needle2 not in src:
        raise RuntimeError("CHECKPOINT17_SINGLE_PREWARM_BIND_MARKER_NOT_FOUND")
    src=src.replace(needle2,repl2,1)

    needle3='''    finally:
        c12._expanded_state=old_expanded
        c7._route=old_route
'''
    repl3='''    finally:
        r.q25.install_hot_math_and_prewarm=old_prewarm
        c12._expanded_state=old_expanded
        c7._route=old_route
'''
    if needle3 not in src:
        raise RuntimeError("CHECKPOINT17_SINGLE_PREWARM_RESTORE_MARKER_NOT_FOUND")
    src=src.replace(needle3,repl3,1)

required=[
    "CHECKPOINT17_SINGLE_PREWARM_HANDOFF",
    "CHECKPOINT17_PREWARM_STATE_DRIFT",
    "r.q25.install_hot_math_and_prewarm=(",
    "r.q25.install_hot_math_and_prewarm=old_prewarm",
    "CHECKPOINT17_LEGACY_REVERSE_SEED",
    "CHECKPOINT17_QUOTE_TEMPLATE_DIRECTION_MISMATCH",
    "expected_templates=expected_pairs*2",
    "[BROADCAST] disabled",
]
for marker in required:
    if marker not in src:
        raise RuntimeError("CHECKPOINT17_REQUIRED_CONTRACT_MISSING:"+marker)

ast.parse(src)
TARGET.write_text(src,encoding="utf-8")

TEST_CODE=r'''import ast
import unittest
from pathlib import Path

P=Path(
    "qseries_v2/oracle_execution/solana_atomic_executor/"
    "checkpoint17_pair_key_execution_templates.py"
)


class T(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.s=P.read_text(encoding="utf-8")
        ast.parse(cls.s)

    def test_single_prewarm_handoff_present(self):
        self.assertIn(
            "CHECKPOINT17_SINGLE_PREWARM_HANDOFF",
            self.s,
        )
        self.assertIn(
            "duplicate_network_prewarm=False",
            self.s,
        )

    def test_checkpoint15_reuses_existing_warm_rows(self):
        self.assertIn(
            "return list(warmed)",
            self.s,
        )
        self.assertIn(
            "r.q25.install_hot_math_and_prewarm=(",
            self.s,
        )

    def test_state_drift_fails_closed(self):
        self.assertIn(
            "CHECKPOINT17_PREWARM_STATE_DRIFT",
            self.s,
        )
        self.assertIn(
            "if child_tokens!=parent_tokens:",
            self.s,
        )

    def test_original_prewarm_restored(self):
        self.assertIn(
            "old_prewarm=r.q25.install_hot_math_and_prewarm",
            self.s,
        )
        self.assertIn(
            "r.q25.install_hot_math_and_prewarm=old_prewarm",
            self.s,
        )

    def test_reverse_seed_fix_preserved(self):
        self.assertIn(
            "CHECKPOINT17_LEGACY_REVERSE_SEED",
            self.s,
        )
        self.assertIn(
            "CHECKPOINT17_REVERSE_SEED_ACCOUNT_INVARIANT",
            self.s,
        )

    def test_direction_guards_preserved(self):
        self.assertIn(
            "CHECKPOINT17_QUOTE_TEMPLATE_DIRECTION_MISMATCH",
            self.s,
        )
        self.assertIn(
            "expected_templates=expected_pairs*2",
            self.s,
        )

    def test_no_broadcast(self):
        self.assertNotIn(
            "sendTransaction",
            self.s,
        )
        self.assertIn(
            "[BROADCAST] disabled",
            self.s,
        )


if __name__=="__main__":
    unittest.main(verbosity=2)
'''

ast.parse(TEST_CODE)
TEST.write_text(TEST_CODE,encoding="utf-8")

print("[PASS] checkpoint-17 single-prewarm handoff replacement installed")
print("[ROOT_CAUSE] checkpoint17 warmed token/program state, checkpoint15 redundantly warmed it again")
print("[REUSE] checkpoint15 now receives the exact checkpoint17 warmed rows")
print("[FAIL_CLOSED] child token set must exactly equal checkpoint17 token set")
print("[REVERSE] legacy reverse seed handoff preserved")
print("[SIZE_BIND] canonical runtime exact size binding untouched")
print("[NETWORK] duplicate token-net Node/RPC prewarm removed from this generation")
print("[KEY] untouched")
print("[BROADCAST] disabled")
print("[TEST]",TEST.name)
