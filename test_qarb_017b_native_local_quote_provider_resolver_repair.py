
import tempfile,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot.native_provider_resolver import *
class T(unittest.TestCase):
    def test_finds_local_provider(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"qseries_v2/x/raydium/clmm";p.mkdir(parents=True)
            (p/"local_math.py").write_text("def quote_exact_in(state,mint,amount):\n return amount\n",encoding="utf-8")
            x=best(td,"RAYDIUM_CLMM");self.assertIsNotNone(x);self.assertTrue(x.hot_io_free)
        print("[PASS] native local quote provider resolver finds I/O-free candidate")
    def test_rejects_http_source(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"qseries_v2/x/orca/whirlpool";p.mkdir(parents=True)
            (p/"bad.py").write_text("import urllib\ndef quote_exact_in(x): return urllib.request.urlopen('x')\n",encoding="utf-8")
            self.assertIsNone(best(td,"ORCA_WHIRLPOOL"))
        print("[PASS] resolver rejects network-dependent quote providers")
if __name__=="__main__": unittest.main(verbosity=2)
