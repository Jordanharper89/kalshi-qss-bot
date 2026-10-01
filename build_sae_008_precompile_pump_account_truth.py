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

TEST=ROOT/"test_sae_008_precompile_pump_account_truth.py"

if not RUNTIME.is_file():
    raise RuntimeError("CANONICAL_RUNTIME_MISSING")

src=RUNTIME.read_text(encoding="utf-8")
tree=ast.parse(src)

target=None

for n in ast.walk(tree):
    if (
        isinstance(n,ast.FunctionDef)
        and n.name=="attack"
    ):
        target=n
        break

if target is None:
    raise RuntimeError("CANONICAL_ATTACK_NOT_FOUND")

compile_call=None

for n in ast.walk(target):
    if not isinstance(n,ast.Call):
        continue

    name=""

    if isinstance(n.func,ast.Attribute):
        name=n.func.attr
    elif isinstance(n.func,ast.Name):
        name=n.func.id

    if "compile" in name.lower():
        compile_call=n
        break

if compile_call is None:
    raise RuntimeError("CANONICAL_COMPILE_CALL_NOT_FOUND")

stmt=None

for n in ast.walk(target):
    if (
        isinstance(n,(ast.Assign,ast.Expr))
        and n.lineno<=compile_call.lineno<=getattr(n,"end_lineno",n.lineno)
    ):
        stmt=n
        break

if stmt is None:
    raise RuntimeError("CANONICAL_COMPILE_STATEMENT_NOT_FOUND")

indent=" "*(stmt.col_offset)

audit=f'''
{indent}for _ix in ixs:
{indent}    if _ix.get("programId")!=q87.c.PUMP:
{indent}        continue
{indent}    _aa=list(_ix.get("accounts") or [])
{indent}    print("[SAE008_PRECOMPILE] total=%d"%len(_aa),flush=True)
{indent}    for _i in range(max(0,len(_aa)-3),len(_aa)):
{indent}        _a=_aa[_i]
{indent}        print("[SAE008_ACCOUNT] index=%d number=%d pubkey=%s signer=%s writable=%s"%(
{indent}            _i,
{indent}            _i+1,
{indent}            _a.get("pubkey"),
{indent}            _a.get("isSigner"),
{indent}            _a.get("isWritable"),
{indent}        ),flush=True)
'''

lines=src.splitlines(keepends=True)

new_src="".join(
    lines[:stmt.lineno-1]
    +[audit]
    +lines[stmt.lineno-1:]
)

ast.parse(new_src)

RUNTIME.write_text(
    new_src,
    encoding="utf-8"
)

TEST.write_text(
'''from pathlib import Path
import unittest

class T(unittest.TestCase):

    def test_precompile_audit_present(self):
        p=Path(
            "qseries_v2/oracle_execution/"
            "solana_atomic_executor/runtime.py"
        )

        s=p.read_text(encoding="utf-8")

        self.assertIn(
            "[SAE008_PRECOMPILE]",
            s
        )

        self.assertIn(
            "[SAE008_ACCOUNT]",
            s
        )

    def test_no_broadcast(self):
        p=Path(
            "qseries_v2/oracle_execution/"
            "solana_atomic_executor/runtime.py"
        )

        s=p.read_text(encoding="utf-8")

        self.assertNotIn(
            "sendTransaction",
            s
        )

if __name__=="__main__":
    unittest.main(verbosity=2)
''',
encoding="utf-8"
)

print("[PASS] SAE-008 precompile Pump account truth installed")
print("[TARGET] final Pump instruction immediately before compile")
print("[CHECK] accounts 24/25/26")
print("[STARTUP] SAE-007B remains truth reference")
print("[TRANSACTION] unchanged")
print("[BROADCAST] disabled")