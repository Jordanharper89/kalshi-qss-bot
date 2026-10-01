from pathlib import Path
import py_compile

ROOT=Path.cwd()
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_money/qarb_clean_bot"
BRIDGE=SUB/"qarb_024_existing_python_atomic_source_bridge.py"
QSB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_money/qsb059_gav_reverse_atomic.py"
BASE=SUB/"qarb_025c_pubkey_serialization_repair.py"

for p in (BRIDGE,QSB,BASE):
    if not p.is_file():
        raise SystemExit("[FAIL] dependency missing: "+str(p))

qsb_src=QSB.read_text(encoding="utf-8")
if "def candidate_instruction_sets(" not in qsb_src:
    raise SystemExit("[FAIL] qsb059 exact candidate_instruction_sets missing")

b=BRIDGE.read_text(encoding="utf-8")
start=b.find("def candidate_instruction_sets(route):")
if start<0:
    raise SystemExit("[FAIL] QARB-024 duplicate candidate normalizer missing")
next_def=b.find("\ndef ",start+5)
if next_def<0:
    raise SystemExit("[FAIL] QARB-024 next function boundary missing")

replacement='def candidate_instruction_sets(route):\n    return load_source().candidate_instruction_sets(route)\n'
b=b[:start]+replacement+b[next_def+1:]
BRIDGE.write_text(b,encoding="utf-8")
py_compile.compile(str(BRIDGE),doraise=True)

s=BASE.read_text(encoding="utf-8")
old='SIZES=tuple(float(x) for x in os.getenv("QARB_025B_SIZES_SOL","0.05,0.1,0.18,0.28,0.5,0.9,1.1,1.4").split(",") if x.strip())'
new='SIZES=tuple(float(x) for x in os.getenv("QARB_025D_SIZES_SOL","0.5").split(",") if x.strip())'
if old not in s:
    raise SystemExit("[FAIL] QARB-025C size-list anchor missing")
s=s.replace(old,new,1)
s=s.replace("[QARB-025C] PUBKEY SERIALIZATION REPAIR",
            "[QARB-025D] EXACT SOURCE CANDIDATE REPAIR",1)
s=s.replace(
    'print("[FIX] composer payer=str(pubkey); packet/simulation payer=Pubkey",flush=True)',
    'print("[FIX] exact qsb059 candidate_instruction_sets; one-size default; no duplicate normalizer",flush=True)',
    1
)

MOD=SUB/"qarb_025d_exact_source_candidate_repair.py"
MOD.write_text(s,encoding="utf-8")
py_compile.compile(str(MOD),doraise=True)

TEST=ROOT/"test_qarb_025d_exact_source_candidate_repair.py"
TEST.write_text('import inspect\nimport unittest\nfrom qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_024_existing_python_atomic_source_bridge as b\nfrom qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_025d_exact_source_candidate_repair as r\n\nclass T(unittest.TestCase):\n    def test_bridge_delegates_to_source(self):\n        src = inspect.getsource(b.candidate_instruction_sets)\n        self.assertIn("load_source().candidate_instruction_sets(route)", src)\n        print("[PASS] QARB-024 now delegates candidate extraction to exact qsb059 source")\n\n    def test_single_size_default(self):\n        self.assertEqual(r.SIZES, (0.5,))\n        print("[PASS] default compose attempts reduced to one size to avoid HTTP hammering")\n\n    def test_execution_false(self):\n        self.assertIs(r.execution_authority, False)\n        print("[PASS] execution_authority=FALSE")\n\nif __name__ == "__main__":\n    unittest.main(verbosity=2)\n',encoding="utf-8")
py_compile.compile(str(TEST),doraise=True)

RUN=ROOT/"run_qarb_025d_exact_source_candidate_repair.py"
RUN.write_text('from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot.qarb_025d_exact_source_candidate_repair import run\nif __name__ == "__main__":\n    run()\n',encoding="utf-8")
py_compile.compile(str(RUN),doraise=True)

print("[PASS] QARB-025D exact-source candidate repair installed")
print("[FIX] removed QARB-024 duplicate candidate normalizer")
print("[SOURCE] qsb059_gav_reverse_atomic.candidate_instruction_sets is now authoritative")
print("[RATE] default compose attempts reduced to one size=0.5 SOL")
print("[FLOW] live pair -> qsb059 compose -> exact qsb059 candidate ladder -> packet gate -> real simulateTransaction")
print("[MODE] execution_authority=FALSE")
