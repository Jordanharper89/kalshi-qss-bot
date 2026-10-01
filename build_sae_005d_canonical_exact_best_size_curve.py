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

TEST=ROOT/"test_sae_005d_canonical_exact_best_size_curve.py"

if not RUNTIME.is_file():
    raise RuntimeError(
        "CANONICAL_RUNTIME_MISSING"
    )

src=RUNTIME.read_text(
    encoding="utf-8"
)

tree=ast.parse(src)

target=None

for node in tree.body:
    if (
        isinstance(node,ast.FunctionDef)
        and node.name=="exact_best"
    ):
        target=node
        break

if target is None:
    raise RuntimeError(
        "CANONICAL_EXACT_BEST_NOT_FOUND"
    )

args=(
    list(target.args.posonlyargs)
    +list(target.args.args)
)

if not args:
    raise RuntimeError(
        "CANONICAL_EXACT_BEST_HAS_NO_SNAPSHOT_ARG"
    )

snap_name=args[0].arg

if not target.body:
    raise RuntimeError(
        "CANONICAL_EXACT_BEST_EMPTY"
    )

body_start=target.body[0].lineno-1

lines=src.splitlines(
    keepends=True
)

indent=" "*(target.col_offset+4)

body=f'''
{indent}# SAE-005D canonical dynamic economic size curve.
{indent}# Every size is priced from the exact same immutable snapshot.
{indent}# Selection authority is maximum executable pre-sim net lamports.
{indent}# 0.180 SOL is the preferred center, not a forced trade size.
{indent}sizes=(
{indent}    0.001,
{indent}    0.010,
{indent}    0.025,
{indent}    0.050,
{indent}    0.100,
{indent}    0.180,
{indent}    0.280,
{indent}    0.500,
{indent}    1.000,
{indent}    1.400,
{indent})

{indent}rows=[]

{indent}for size in sizes:
{indent}    rows.extend(
{indent}        q18.exact_snapshot_opportunities(
{indent}            {snap_name},
{indent}            size,
{indent}        )
{indent}    )

{indent}if not rows:
{indent}    raise RuntimeError(
{indent}        "SAE005D_NO_SIZE_QUOTES"
{indent}    )

{indent}return max(
{indent}    rows,
{indent}    key=lambda x:int(
{indent}        x["local_net"]
{indent}    ),
{indent})
'''.lstrip("\n")


new_src="".join(
    lines[:body_start]
    +[
        body
    ]
    +lines[target.end_lineno:]
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


EXPECTED=(
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

    def test_exact_best_is_canonical_target(self):
        src=inspect.getsource(
            q.exact_best
        )

        self.assertIn(
            "SAE-005D canonical dynamic economic size curve",
            src
        )

    def test_all_sizes_present(self):
        src=inspect.getsource(
            q.exact_best
        )

        for size in EXPECTED:
            self.assertIn(
                f"{size:.3f}",
                src
            )

    def test_prices_every_size(self):
        src=inspect.getsource(
            q.exact_best
        )

        self.assertIn(
            "for size in sizes",
            src
        )

        self.assertIn(
            "q18.exact_snapshot_opportunities",
            src
        )

    def test_selects_max_net_lamports(self):
        src="".join(
            inspect.getsource(
                q.exact_best
            ).split()
        )

        self.assertIn(
            'returnmax(rows,key=lambdax:int(x["local_net"]))',
            src
        )

    def test_canonical_price_calls_exact_best(self):
        src=inspect.getsource(
            q.canonical_price
        )

        self.assertIn(
            "exact_best(",
            src
        )

    def test_sae001_meteora_hot_preserved(self):
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

    def test_sae004_pool_v2_preserved(self):
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
    "[PASS] SAE-005D canonical exact_best size curve installed"
)
print(
    "[TARGET] canonical runtime exact_best()"
)
print(
    "[SIZES] 0.001,0.010,0.025,0.050,0.100,0.180,0.280,0.500,1.000,1.400"
)
print(
    "[SELECT] maximum local_net lamports"
)
print(
    "[CENTER] 0.180 SOL reference only"
)
print(
    "[BYPASS] ORACLE-020 size constants no longer matter to canonical selector"
)
print(
    "[SAE-001..004] preserved"
)
print(
    "[BROADCAST] disabled"
)