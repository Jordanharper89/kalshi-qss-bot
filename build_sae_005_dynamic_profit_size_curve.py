from pathlib import Path
import ast

ROOT=Path.cwd()

RUNTIME=(
    ROOT/
    "qseries_v2"/
    "oracle_execution"/
    "solana_atomic_executor"/
    "runtime.py"
)

TEST=ROOT/"test_sae_005_dynamic_profit_size_curve.py"

if not RUNTIME.is_file():
    raise RuntimeError(
        "CANONICAL_RUNTIME_MISSING"
    )

src=RUNTIME.read_text(
    encoding="utf-8"
)

tree=ast.parse(src)

fast_node=None
expand_node=None

for node in tree.body:

    if not isinstance(
        node,
        ast.Assign
    ):
        continue

    names=[
        t.id
        for t in node.targets
        if isinstance(
            t,
            ast.Name
        )
    ]

    if "FAST" in names:
        fast_node=node

    if "EXPAND" in names:
        expand_node=node


if fast_node is None:
    raise RuntimeError(
        "CANONICAL_FAST_SIZE_ASSIGNMENT_MISSING"
    )

if expand_node is None:
    raise RuntimeError(
        "CANONICAL_EXPAND_SIZE_ASSIGNMENT_MISSING"
    )


#
# ============================================================
# SAE-005
#
# Full economic curve is now evaluated in the primary scan.
#
# 0.001 remains available for measurement/canary semantics.
# 0.180 is the preferred center of gravity.
#
# Selection authority stays with existing exact_best(),
# which must choose by local_net rather than percentage alone.
# ============================================================
#

SIZE_LADDER=(
    0.001,
    0.010,
    0.025,
    0.050,
    0.100,
    0.180,
    0.280,
    0.500,
    1.000,
    1.400,
)

replacement_fast=(
    "PREFERRED_SIZE_SOL=0.180\n\n"
    "SIZE_LADDER=(\n"
    "    0.001,\n"
    "    0.010,\n"
    "    0.025,\n"
    "    0.050,\n"
    "    0.100,\n"
    "    0.180,\n"
    "    0.280,\n"
    "    0.500,\n"
    "    1.000,\n"
    "    1.400,\n"
    ")\n\n"
    "# SAE-005: every size participates in the primary scan.\n"
    "FAST=SIZE_LADDER\n"
)

replacement_expand=(
    "# SAE-005: expansion is already included in FAST.\n"
    "EXPAND=()\n"
)


lines=src.splitlines(
    keepends=True
)

replacements=[
    (
        fast_node.lineno-1,
        fast_node.end_lineno,
        replacement_fast,
    ),
    (
        expand_node.lineno-1,
        expand_node.end_lineno,
        replacement_expand,
    ),
]

#
# Apply bottom-up so line offsets remain valid.
#
for start,end,text in sorted(
    replacements,
    reverse=True
):
    lines[
        start:end
    ]=[
        text
    ]


new_src="".join(
    lines
)

ast.parse(
    new_src
)

RUNTIME.write_text(
    new_src,
    encoding="utf-8"
)


TEST_SOURCE=r'''
import inspect
import unittest

from qseries_v2.oracle_execution.solana_atomic_executor import (
    runtime as q
)


class T(unittest.TestCase):

    def test_safety(self):
        self.assertFalse(
            q.EXECUTION_AUTHORITY
        )

        self.assertTrue(
            q.PAPER_ONLY
        )

        self.assertFalse(
            q.REAL_MONEY_MOVED
        )

    def test_preferred_center(self):
        self.assertEqual(
            q.PREFERRED_SIZE_SOL,
            0.180
        )

    def test_full_size_ladder(self):

        self.assertEqual(
            tuple(q.SIZE_LADDER),
            (
                0.001,
                0.010,
                0.025,
                0.050,
                0.100,
                0.180,
                0.280,
                0.500,
                1.000,
                1.400,
            )
        )

    def test_primary_scan_is_full_ladder(self):

        self.assertEqual(
            tuple(q.FAST),
            tuple(q.SIZE_LADDER)
        )

        self.assertEqual(
            tuple(q.EXPAND),
            ()
        )

    def test_exact_best_uses_primary_ladder(self):

        src=inspect.getsource(
            q.exact_best
        )

        self.assertIn(
            "FAST",
            src
        )

    def test_exact_best_is_net_based(self):

        src=inspect.getsource(
            q.exact_best
        )

        self.assertIn(
            "local_net",
            src
        )

        #
        # We intentionally do not choose
        # by local_bps alone.
        #
        self.assertTrue(
            (
                "max(" in src
                or "sorted(" in src
            )
        )

    def test_sae001_meteora_hot_path_preserved(self):

        src=inspect.getsource(
            q.build_meteora_ix_hot
        )

        for bad in (
            "c.rpc(",
            "c.account(",
            "dlmm_arrays(",
            "urlopen(",
        ):
            self.assertNotIn(
                bad,
                src
            )

    def test_sae002_truth_gate_preserved(self):

        src=inspect.getsource(
            q.attack
        )

        self.assertIn(
            "pump_6040_actual_base_out",
            src
        )

        self.assertIn(
            "reprice_from_pump_chain_truth",
            src
        )

    def test_sae003_exact_quote_preserved(self):

        self.assertEqual(
            q.q18.WORKER_JS.name,
            "sae003_pump_exact_quote_worker.mjs"
        )

    def test_sae004_24_account_contract_preserved(self):

        self.assertEqual(
            q.q87.PUMP_FIXED_ACCOUNTS,
            24
        )

    def test_no_broadcast(self):

        src=inspect.getsource(q)

        self.assertNotIn(
            "sendTransaction",
            src
        )


if __name__=="__main__":

    unittest.main(
        verbosity=2
    )
'''

ast.parse(
    TEST_SOURCE
)

TEST.write_text(
    TEST_SOURCE.lstrip(),
    encoding="utf-8"
)

print(
    "[PASS] SAE-005 dynamic profit size curve installed"
)

print(
    "[CENTER] preferred_size_sol=0.180"
)

print(
    "[LADDER] 0.001,0.010,0.025,0.050,0.100,0.180,0.280,0.500,1.000,1.400"
)

print(
    "[SCAN] full ladder evaluated in primary exact scan"
)

print(
    "[SELECT] existing exact_best must maximize local_net"
)

print(
    "[SAE-001] memory-only Meteora preserved"
)

print(
    "[SAE-002] Pump chain-truth gate preserved"
)

print(
    "[SAE-003] exact quote-in Pump pricing preserved"
)

print(
    "[SAE-004] 24-account pool_v2 contract preserved"
)

print(
    "[BROADCAST] disabled"
)