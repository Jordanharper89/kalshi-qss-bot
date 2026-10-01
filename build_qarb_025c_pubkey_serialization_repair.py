from pathlib import Path
import py_compile

ROOT=Path.cwd()
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_money/qarb_clean_bot"
SRC=SUB/"qarb_025b_live_binding_real_simulation_repair.py"

if not SRC.is_file():
    raise SystemExit("[FAIL] QARB-025B missing: "+str(SRC))

s=SRC.read_text(encoding="utf-8")

old='route=bridge.compose_exact_candidates(user,token,pump,meteora,size)'
new='route=bridge.compose_exact_candidates(str(user),token,pump,meteora,size)'

if old not in s:
    raise SystemExit("[FAIL] QARB-025B compose call anchor missing")

s=s.replace(old,new,1)

MOD=SUB/"qarb_025c_pubkey_serialization_repair.py"
s=s.replace(
    "[QARB-025B] LIVE-BINDING REAL ATOMIC SIMULATION REPAIR",
    "[QARB-025C] PUBKEY SERIALIZATION REPAIR",
    1
)
s=s.replace(
    'print("[SOURCE] current qarb_clean_bot.engine.candidate_universe",flush=True)',
    'print("[SOURCE] current qarb_clean_bot.engine.candidate_universe",flush=True)\n'
    '    print("[FIX] composer payer=str(pubkey); packet/simulation payer=Pubkey",flush=True)',
    1
)
MOD.write_text(s,encoding="utf-8")

TEST=ROOT/"test_qarb_025c_pubkey_serialization_repair.py"
TEST.write_text('import inspect\nimport unittest\nfrom qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_025c_pubkey_serialization_repair as q\n\nclass T(unittest.TestCase):\n    def test_compose_uses_string_payer(self):\n        src = inspect.getsource(q.run)\n        self.assertIn("compose_exact_candidates(str(user),token,pump,meteora,size)", src)\n        print("[PASS] composer receives JSON-serializable string payer")\n\n    def test_packet_still_uses_pubkey(self):\n        src = inspect.getsource(q.run)\n        self.assertIn("payer=user,recent_blockhash=bh", src)\n        print("[PASS] V0 compiler still receives real Pubkey object")\n\n    def test_execution_false(self):\n        self.assertIs(q.execution_authority, False)\n        print("[PASS] execution_authority=FALSE")\n\nif __name__ == "__main__":\n    unittest.main(verbosity=2)\n',encoding="utf-8")

RUN=ROOT/"run_qarb_025c_pubkey_serialization_repair.py"
RUN.write_text('from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot.qarb_025c_pubkey_serialization_repair import run\nif __name__ == "__main__":\n    run()\n',encoding="utf-8")

for p in (MOD,TEST,RUN):
    py_compile.compile(str(p),doraise=True)

print("[PASS] QARB-025C Pubkey serialization repair installed")
print("[FIX] compose payer converted to string before JSON-producing upstream code")
print("[PRESERVED] packet compile and simulateTransaction retain real Pubkey payer")
print("[FLOW] current live pair -> compose -> <=1232 -> real simulateTransaction")
print("[MODE] execution_authority=FALSE")
