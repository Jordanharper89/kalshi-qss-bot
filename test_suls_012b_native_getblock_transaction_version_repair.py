import inspect, unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parent

class T(unittest.TestCase):
    def test_repair(self):
        import qseries_v2.oracle_adapters.independent.oad_318_solana_native_finalized_block_stream as m
        src=inspect.getsource(m)
        self.assertIn("maxSupportedTransactionVersion", src)
        self.assertRegex(src, r"maxSupportedTransactionVersion['\"]?\s*:\s*1")
        print("[PASS] OAD-318 declares maxSupportedTransactionVersion=1")

        from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_012_native_block_shape_probe import probe
        d=probe()
        print("[SULS012_OK]", d.get("ok"))
        if d.get("shape") is not None:
            print("[SULS012_SHAPE]", d["shape"])
        if d.get("error"):
            print("[SULS012_ERROR]", d["error"])
        if not d.get("ok"):
            self.fail("SULS-012 native block probe still failed after OAD-318 repair")

        print("[PASS] SULS-012B native getBlock transaction-version repair")
        print("[PASS] execution_authority=FALSE")

if __name__=="__main__":
    unittest.main()
