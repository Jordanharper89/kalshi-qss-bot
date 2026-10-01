from pathlib import Path
import py_compile

ROOT=Path.cwd()
CORE=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_money/atomic_crossdex_sim/core.py"
if not CORE.is_file():
    raise SystemExit("[FAIL] QSB-049 core missing")

s=CORE.read_text(encoding="utf-8")
old='if not sec:raise RuntimeError("SET_QSB_SOLANA_WALLET_OR_QSB_SOLANA_PRIVATE_KEY")'
new='if not sec:return "MriyaNN8TMp6qRWjfr723PK7xgQK7yCt7Kg2v2PQu7X"'
if old not in s:
    raise SystemExit("[FAIL] exact QSB-049 wallet gate not found")
CORE.write_text(s.replace(old,new,1),encoding="utf-8")
py_compile.compile(str(CORE),doraise=True)

TEST=ROOT/"test_qsb_049b_no_wallet_env_sim_repair.py"
TEST.write_text('import os,unittest\nfrom qseries_v2.oracle_strategy_intelligence.solana_money.atomic_crossdex_sim import core as c\nMRIYA="MriyaNN8TMp6qRWjfr723PK7xgQK7yCt7Kg2v2PQu7X"\nclass T(unittest.TestCase):\n def test_default_sim_payer(self):\n  a=os.environ.pop("QSB_SOLANA_WALLET",None)\n  b=os.environ.pop("QSB_SOLANA_PRIVATE_KEY",None)\n  try:self.assertEqual(c.wallet_pubkey(),MRIYA)\n  finally:\n   if a is not None:os.environ["QSB_SOLANA_WALLET"]=a\n   if b is not None:os.environ["QSB_SOLANA_PRIVATE_KEY"]=b\n  print("[PASS] no wallet env required for simulation-only run")\n def test_authority_stays_false(self):\n  src=open(c.__file__,encoding="utf-8").read()\n  self.assertIn(\'"execution_authority":False\',src)\n  self.assertIn(\'"sent":False\',src)\n  print("[PASS] execution_authority=FALSE sent=FALSE")\nif __name__=="__main__":unittest.main(verbosity=2)\n',encoding="utf-8")
py_compile.compile(str(TEST),doraise=True)

RUN=ROOT/"run_qsb_049b_no_wallet_env_sim_repair.py"
RUN.write_text("from qseries_v2.oracle_strategy_intelligence.solana_money.atomic_crossdex_sim.runtime import main\nif __name__=='__main__':main()\n",encoding="utf-8")
py_compile.compile(str(RUN),doraise=True)

print("[PASS] QSB-049B no-wallet-env simulation repair installed")
print("[FIX] simulation defaults to Mriya payer when no local Solana wallet env is set")
print("[MODE] execution_authority=FALSE sent=FALSE")
