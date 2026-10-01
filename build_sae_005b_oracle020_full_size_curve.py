from pathlib import Path
import ast

ROOT=Path.cwd()

Q20=(
    ROOT/
    "qseries_v2"/
    "oracle_execution"/
    "oracle_020_latest_state_exact_pricing_worker.py"
)

TEST=ROOT/"test_sae_005b_oracle020_full_size_curve.py"

if not Q20.is_file():
    raise RuntimeError(
        "ORACLE020_SOURCE_MISSING:"
        +str(Q20)
    )

src=Q20.read_text(
    encoding="utf-8"
)

tree=ast.parse(src)

assignments={}

for node in tree.body:
    if not isinstance(
        node,
        ast.Assign
    ):
        continue

    for target in node.targets:
        if isinstance(
            target,
            ast.Name
        ):
            assignments[
                target.id
            ]=node

required=(
    "FAST_SIZES",
    "EXPAND_SIZES",
    "EXPAND_GATE_BPS",
)

missing=[
    name
    for name in required
    if name not in assignments
]

if missing:
    raise RuntimeError(
        "ORACLE020_SIZE_ASSIGNMENTS_MISSING:"
        +",".join(missing)
    )


#
# ============================================================
# SAE-005B
#
# FULL ECONOMIC SIZE CURVE
#
# All sizes are evaluated from the SAME immutable snapshot.
# Selection remains:
#
#     max(rows,key=lambda x:x["local_net"])
#
# 0.180 SOL is the center/reference size, not a forced winner.
# ============================================================
#

replacement={
    "FAST_SIZES":'''PREFERRED_SIZE_SOL=0.180

FULL_SIZE_CURVE=(
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

FAST_SIZES=FULL_SIZE_CURVE
''',

    "EXPAND_SIZES":'''EXPAND_SIZES=()
''',

    #
    # The expansion branch becomes inert because
    # EXPAND_SIZES is empty. Keep the symbol so
    # existing source contracts remain valid.
    #
    "EXPAND_GATE_BPS":'''EXPAND_GATE_BPS=-1000000.0
''',
}


lines=src.splitlines(
    keepends=True
)

patches=[]

for name,text in replacement.items():

    node=assignments[name]

    patches.append(
        (
            node.lineno-1,
            node.end_lineno,
            text,
        )
    )


for start,end,text in sorted(
    patches,
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

Q20.write_text(
    new_src,
    encoding="utf-8"
)


TEST_SOURCE=r'''
import inspect
import unittest

from qseries_v2.oracle_execution import (
    oracle_020_latest_state_exact_pricing_worker
    as q20
)

from qseries_v2.oracle_execution.solana_atomic_executor import (
    runtime as canonical
)


class T(unittest.TestCase):

    def test_safety(self):

        self.assertFalse(
            q20.EXECUTION_AUTHORITY
        )

        self.assertTrue(
            q20.PAPER_ONLY
        )

        self.assertFalse(
            q20.REAL_MONEY_MOVED
        )

        self.assertFalse(
            canonical.EXECUTION_AUTHORITY
        )

    def test_preferred_center(self):

        self.assertEqual(
            q20.PREFERRED_SIZE_SOL,
            0.180
        )

    def test_full_curve_exact(self):

        self.assertEqual(
            tuple(
                q20.FULL_SIZE_CURVE
            ),
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

    def test_every_size_is_primary(self):

        self.assertEqual(
            tuple(
                q20.FAST_SIZES
            ),
            tuple(
                q20.FULL_SIZE_CURVE
            )
        )

        self.assertEqual(
            tuple(
                q20.EXPAND_SIZES
            ),
            ()
        )

    def test_selection_is_max_net_lamports(self):

        src=inspect.getsource(
            q20.LatestStateLane._price
        )

        self.assertIn(
            'max(rows,key=lambda x:x["local_net"])',
            src.replace(
                " ",
                ""
            )
        )

    def test_every_primary_size_is_quoted(self):

        src=inspect.getsource(
            q20.LatestStateLane._price
        )

        self.assertIn(
            "for size in FAST_SIZES",
            src
        )

        self.assertIn(
            "q18.exact_snapshot_opportunities",
            src
        )

    def test_sae003_pricer_preserved(self):

        self.assertEqual(
            canonical.q18.WORKER_JS.name,
            "sae003_pump_exact_quote_worker.mjs"
        )

    def test_sae004_pump_contract_preserved(self):

        self.assertEqual(
            canonical.q87.PUMP_FIXED_ACCOUNTS,
            24
        )

    def test_hot_meteora_stays_rpc_free(self):

        src=inspect.getsource(
            canonical.build_meteora_ix_hot
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
            canonical.attack
        )

        self.assertIn(
            "pump_6040_actual_base_out",
            src
        )

        self.assertIn(
            "reprice_from_pump_chain_truth",
            src
        )

    def test_no_broadcast(self):

        src=inspect.getsource(
            canonical
        )

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
    "[PASS] SAE-005B ORACLE-020 full dynamic size curve installed"
)

print(
    "[TARGET] oracle_020_latest_state_exact_pricing_worker.py"
)

print(
    "[CENTER] preferred_size_sol=0.180"
)

print(
    "[PRIMARY] 0.001,0.010,0.025,0.050,0.100,0.180,0.280,0.500,1.000,1.400"
)

print(
    "[EXPANSION] retired; every size evaluated directly"
)

print(
    "[SELECT] maximum local_net lamports"
)

print(
    "[SAE-001] memory-only Meteora preserved"
)

print(
    "[SAE-002] chain-truth gate preserved"
)

print(
    "[SAE-003] exact quote-in Pump pricing preserved"
)

print(
    "[SAE-004] pool_v2 24-account boundary preserved"
)

print(
    "[BROADCAST] disabled"
)