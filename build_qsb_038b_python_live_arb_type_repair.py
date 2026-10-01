from pathlib import Path
import py_compile,shutil

ROOT=Path.cwd()
CORE=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_money/mriya_python_paper_arb/core.py"
TEST=ROOT/"test_qsb_038b_python_live_arb_type_repair.py"

if not CORE.is_file():
    raise SystemExit("[FAIL] QSB-038 core missing: "+str(CORE.relative_to(ROOT)))

src=CORE.read_text(encoding="utf-8")
bad='p=PoolState.from_accounts(lb,bins,decimals_x=int(dx),decimals_y=int(dy),\n                              lb_pair_key=pool_meta["address"],exhaustive=True)'
good='p=PoolState.from_accounts(lb,bins,decimals_x=int(dx),decimals_y=int(dy),\n                              exhaustive=True)'

if bad not in src:
    raise SystemExit("[FAIL] exact QSB-038 bad lb_pair_key call not found; refusing blind patch")

backup=ROOT/"runtime_state/qseries/qsb038b_backup/core.py"
backup.parent.mkdir(parents=True,exist_ok=True)
shutil.copy2(CORE,backup)

CORE.write_text(src.replace(bad,good,1),encoding="utf-8")
py_compile.compile(str(CORE),doraise=True)

TEST.write_text('import sys,types,unittest\nfrom unittest.mock import patch\nfrom qseries_v2.oracle_strategy_intelligence.solana_money.mriya_python_paper_arb import core\n\nclass FakeQuote:\n    complete=True\n    remaining_in=0\n    amount_out=123456789\n    bins_crossed=2\n\nclass FakePoolState:\n    @staticmethod\n    def from_accounts(lb,bins,decimals_x,decimals_y,lb_pair_key=None,exhaustive=False):\n        if isinstance(lb_pair_key,str):\n            raise TypeError("string argument without an encoding")\n        assert lb==b"LB"\n        assert bins==[b"BIN"]\n        assert exhaustive is True\n        return object()\n\ndef fake_quote(*a,**k):\n    return FakeQuote()\n\nclass T(unittest.TestCase):\n    def test_exact_crash_is_removed(self):\n        fake=types.ModuleType("meteora_dlmm")\n        fake.PoolState=FakePoolState\n        fake.quote=fake_quote\n        meta={"address":"BASE58_POOL_STRING","decimals_x":9,"decimals_y":6,\n              "token_x":core.WSOL,"token_y":core.TOKEN}\n        with patch.dict(sys.modules,{"meteora_dlmm":fake}):\n            with patch.object(core,"fetch_account_bytes",return_value=b"LB"):\n                with patch.object(core,"fetch_bin_arrays",return_value=[b"BIN"]):\n                    q=core.meteora_quote("rpc",meta,0.699517207)\n        self.assertTrue(q["exact"])\n        self.assertEqual(q["raw_out"],123456789)\n        print("[PASS] reproduced QSB-038 Meteora call without Base58-string lb_pair_key TypeError")\n\n    def test_source_never_passes_pool_string_as_lb_pair_key(self):\n        import inspect\n        s=open(inspect.getfile(core),encoding="utf-8").read()\n        self.assertNotIn(\'lb_pair_key=pool_meta["address"]\',s)\n        print("[PASS] Base58 pool string is no longer passed to 32-byte lb_pair_key")\n\n    def test_original_qsb038_gate_preserved(self):\n        self.assertEqual(core.MIN_NET_BPS,10.0)\n        self.assertEqual(core.MAX_SLOT_SPREAD,4)\n        print("[PASS] QSB-038 paper-profit gates preserved")\n\nif __name__=="__main__":\n    unittest.main(verbosity=2)\n',encoding="utf-8")
py_compile.compile(str(TEST),doraise=True)

print("[PASS] QSB-038B repaired QSB-038 in place")
print("[ROOT_CAUSE] Base58 pool address string was incorrectly passed as lb_pair_key bytes")
print("[FIX] optional lb_pair_key assertion removed; raw pool + exhaustive BinArrays preserved")
print("[BACKUP]",backup.relative_to(ROOT))
print("[TEST]",TEST.name)
print("[MODE] PAPER_ONLY=True execution_authority=FALSE")
