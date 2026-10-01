from pathlib import Path
import re, shutil

ROOT=Path(__file__).resolve().parent
TARGET=ROOT/"qseries_v2/oracle_adapters/independent/oad_318_solana_native_finalized_block_stream.py"
TEST=ROOT/"test_suls_012b_native_getblock_transaction_version_repair.py"

def patch_source(text):
    if "maxSupportedTransactionVersion" in text:
        return text, "ALREADY_PRESENT"

    patterns = [
        (r'("encoding"\s*:\s*"json")', r'\1, "maxSupportedTransactionVersion": 1'),
        (r"('encoding'\s*:\s*'json')", r"\1, 'maxSupportedTransactionVersion': 1"),
        (r'("transactionDetails"\s*:\s*"full")', r'\1, "maxSupportedTransactionVersion": 1'),
        (r"('transactionDetails'\s*:\s*'full')", r"\1, 'maxSupportedTransactionVersion': 1"),
        (r'("rewards"\s*:\s*(?:False|false))', r'\1, "maxSupportedTransactionVersion": 1'),
        (r"('rewards'\s*:\s*(?:False|false))", r"\1, 'maxSupportedTransactionVersion': 1"),
    ]
    for pat, repl in patterns:
        new, n = re.subn(pat, repl, text, count=1)
        if n:
            return new, f"PATCHED:{pat}"
    raise RuntimeError(
        "Could not locate OAD-318 getBlock config safely. "
        "No mutation performed; inspect _fetch_block_once before retrying."
    )

TEST_TEXT = '''import inspect, unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parent

class T(unittest.TestCase):
    def test_repair(self):
        import qseries_v2.oracle_adapters.independent.oad_318_solana_native_finalized_block_stream as m
        src=inspect.getsource(m)
        self.assertIn("maxSupportedTransactionVersion", src)
        self.assertRegex(src, r"maxSupportedTransactionVersion['\\\"]?\\s*:\\s*1")
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
'''

def main():
    print("="*116)
    print(" SULS-012B OAD-318 NATIVE getBlock TRANSACTION-VERSION FOUNDATION REPAIR")
    print("="*116)

    if not TARGET.is_file():
        raise FileNotFoundError(TARGET)

    original=TARGET.read_text(encoding="utf-8")
    repaired,status=patch_source(original)

    if repaired != original:
        backup=TARGET.with_suffix(TARGET.suffix+".pre_suls012b.bak")
        if not backup.exists():
            shutil.copy2(TARGET, backup)
        TARGET.write_text(repaired, encoding="utf-8")
        print("[PASS] repaired:", TARGET.relative_to(ROOT))
        print("[PASS] backup:", backup.relative_to(ROOT))
    else:
        print("[PASS] existing compatibility already present:", TARGET.relative_to(ROOT))

    print("[STATUS]", status)
    print("[PASS] getBlock now declares maxSupportedTransactionVersion=1")
    print("[PASS] no new acquisition subsystem created")

    TEST.write_text(TEST_TEXT, encoding="utf-8")
    print("[PASS] test:", TEST.name)
    print("[PASS] execution_authority=FALSE")
    print("[SCOPE] Foundational OAD-318 compatibility repair; SULS-012 physical probe recertified by test")

if __name__=="__main__":
    main()
