from pathlib import Path
import ast,py_compile

ROOT=Path.cwd()
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_money/qarb_clean_bot"
BRIDGE=SUB/"qarb_024_existing_python_atomic_source_bridge.py"
QSB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_money/qsb059_gav_reverse_atomic.py"
BASE=SUB/"qarb_025c_pubkey_serialization_repair.py"

for p in (BRIDGE,QSB,BASE):
    if not p.is_file():
        raise SystemExit("[FAIL] dependency missing: "+str(p))

qsb_text=QSB.read_text(encoding="utf-8")
qsb_tree=ast.parse(qsb_text)
qsb_fn=next((n for n in qsb_tree.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name=="candidate_instruction_sets"),None)
if qsb_fn is None:
    raise SystemExit("[FAIL] exact qsb059 candidate_instruction_sets not found")

bridge_text=BRIDGE.read_text(encoding="utf-8")
bridge_tree=ast.parse(bridge_text)
target=next((n for n in bridge_tree.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name=="candidate_instruction_sets"),None)
if target is None:
    raise SystemExit("[FAIL] QARB-024 candidate_instruction_sets function not found")

lines=bridge_text.splitlines(keepends=True)
start=target.lineno-1
end=target.end_lineno
replacement=[
    "def candidate_instruction_sets(route):\n",
    "    return load_source().candidate_instruction_sets(route)\n",
]
new_text="".join(lines[:start]+replacement+lines[end:])
BRIDGE.write_text(new_text,encoding="utf-8")
py_compile.compile(str(BRIDGE),doraise=True)

check=BRIDGE.read_text(encoding="utf-8")
if "return load_source().candidate_instruction_sets(route)" not in check:
    raise SystemExit("[FAIL] bridge delegation repair not present after write")

s=BASE.read_text(encoding="utf-8")
old='os.getenv("QARB_025B_SIZES_SOL","0.05,0.1,0.18,0.28,0.5,0.9,1.1,1.4")'
new='os.getenv("QARB_025E_SIZES_SOL","0.5")'
if old not in s:
    raise SystemExit("[FAIL] QARB-025C size config anchor missing")
s=s.replace(old,new,1)
s=s.replace("[QARB-025C] PUBKEY SERIALIZATION REPAIR",
            "[QARB-025E] AST EXACT CANDIDATE REPAIR",1)
s=s.replace(
    'print("[FIX] composer payer=str(pubkey); packet/simulation payer=Pubkey",flush=True)',
    'print("[FIX] AST bridge delegation -> exact qsb059 candidate ladder; one-size default",flush=True)',
    1
)

MOD=SUB/"qarb_025e_ast_exact_candidate_repair.py"
MOD.write_text(s,encoding="utf-8")
py_compile.compile(str(MOD),doraise=True)

TEST=ROOT/"test_qarb_025e_ast_exact_candidate_repair.py"
TEST.write_text('import inspect\nimport unittest\nfrom qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_024_existing_python_atomic_source_bridge as b\nfrom qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_025e_ast_exact_candidate_repair as r\n\nclass T(unittest.TestCase):\n    def test_bridge_delegates_exact_source(self):\n        src = inspect.getsource(b.candidate_instruction_sets)\n        self.assertIn("load_source().candidate_instruction_sets(route)", src)\n        print("[PASS] bridge delegates to exact qsb059 candidate_instruction_sets")\n\n    def test_single_size_default(self):\n        self.assertEqual(r.SIZES, (0.5,))\n        print("[PASS] one-size default avoids HTTP hammering")\n\n    def test_execution_false(self):\n        self.assertIs(r.execution_authority, False)\n        print("[PASS] execution_authority=FALSE")\n\nif __name__ == "__main__":\n    unittest.main(verbosity=2)\n',encoding="utf-8")
py_compile.compile(str(TEST),doraise=True)

RUN=ROOT/"run_qarb_025e_ast_exact_candidate_repair.py"
RUN.write_text('from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot.qarb_025e_ast_exact_candidate_repair import run\nif __name__ == "__main__":\n    run()\n',encoding="utf-8")
py_compile.compile(str(RUN),doraise=True)

print("[PASS] QARB-025E AST exact-candidate repair installed")
print("[PATCH] located QARB-024 candidate_instruction_sets by AST function name")
print("[SOURCE] qsb059_gav_reverse_atomic.candidate_instruction_sets authoritative")
print("[RATE] default compose size=0.5 SOL only")
print("[FLOW] live pair -> exact qsb059 candidates -> packet gate -> real simulateTransaction")
print("[MODE] execution_authority=FALSE")
