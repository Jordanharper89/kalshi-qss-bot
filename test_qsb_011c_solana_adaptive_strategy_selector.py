import json,tempfile,unittest
from pathlib import Path
from qseries_v2.solana_windows_safe_provider import WindowsSafeUniversalProvider

class T(unittest.TestCase):
    def test_cache_failure_never_crashes_provider(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            p=WindowsSafeUniversalProvider(root)
            # Force persistence failure by making cache_path a directory.
            bad=root/"runtime_state/qseries/solana_adaptive_runtime_v3/universe_cache.json"
            bad.mkdir(parents=True,exist_ok=True)
            p.cache_path=bad
            p.tokens=["TOKEN1"];p.last_refresh=1.0;p.cursor=1
            ok=p._persist()
            self.assertFalse(ok)
            self.assertEqual(p.cache_persist_errors,1)
            self.assertEqual(p.tokens,["TOKEN1"])
            print("[PASS] cache persistence failure is non-fatal; in-memory universe survives")

if __name__=="__main__":unittest.main()
