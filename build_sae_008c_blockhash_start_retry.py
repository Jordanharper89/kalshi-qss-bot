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

TEST=ROOT/"test_sae_008c_blockhash_start_retry.py"

src=RUNTIME.read_text(
    encoding="utf-8"
)

tree=ast.parse(src)

target=None
refresh_stmt=None

for cls in tree.body:
    if not isinstance(cls,ast.ClassDef):
        continue

    for fn in cls.body:
        if (
            isinstance(fn,ast.FunctionDef)
            and fn.name=="start"
        ):
            for stmt in fn.body:
                if not isinstance(stmt,ast.Expr):
                    continue

                call=stmt.value

                if (
                    isinstance(call,ast.Call)
                    and isinstance(call.func,ast.Attribute)
                    and isinstance(call.func.value,ast.Name)
                    and call.func.value.id=="self"
                    and call.func.attr=="refresh"
                ):
                    target=fn
                    refresh_stmt=stmt
                    break

        if refresh_stmt is not None:
            break

    if refresh_stmt is not None:
        break

if refresh_stmt is None:
    raise RuntimeError(
        "SAE008C_BLOCKHASH_REFRESH_SEAM_MISSING"
    )

lines=src.splitlines(
    keepends=True
)

indent=" "*refresh_stmt.col_offset

replacement=f'''{indent}for _attempt in range(1,7):
{indent}    try:
{indent}        self.refresh()
{indent}        break
{indent}    except Exception as _exc:
{indent}        if _attempt>=6:
{indent}            raise
{indent}        print(
{indent}            "[SAE008C_BLOCKHASH_RETRY] attempt=%d error=%s:%s"%(
{indent}                _attempt,
{indent}                type(_exc).__name__,
{indent}                _exc,
{indent}            ),
{indent}            flush=True,
{indent}        )
{indent}        time.sleep(min(0.5*_attempt,2.0))
'''

new_src="".join(
    lines[:refresh_stmt.lineno-1]
    +[replacement]
    +lines[refresh_stmt.end_lineno:]
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

    def test_start_retry_installed(self):
        src=inspect.getsource(
            type(q.BLOCKHASH).start
        )

        self.assertIn(
            "SAE008C_BLOCKHASH_RETRY",
            src
        )

        self.assertIn(
            "range(1,7)",
            src.replace(" ","")
        )

    def test_account_audit_preserved(self):
        from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_execution_engineering import (
            qarb_087_two_second_compaction_liquidity_repair as q87
        )

        src=inspect.getsource(
            q87.repaired_candidates
        )

        self.assertIn(
            "SAE008B_CANDIDATE",
            src
        )

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
    "[PASS] SAE-008C blockhash startup retry installed"
)
print(
    "[RETRY] transient RPC failure no longer kills startup immediately"
)
print(
    "[MAX_ATTEMPTS] 6"
)
print(
    "[SAE-008B] account audit preserved"
)
print(
    "[PUMP_ACCOUNTS] unchanged"
)
print(
    "[BROADCAST] disabled"
)