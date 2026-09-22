from pathlib import Path
from qseries_v2.oracle_coinbase_high_frequency.chf_008_single_writer_contract_discovery import discover
report,path=discover(Path.cwd())
print("[REPORT]",path)
for module in report["modules"]:
    print("[MODULE]",module["module"],"imported=",module["imported"])
    for fn in module["functions"]:
        print("[FUNCTION]",fn["name"],fn["signature"])
    for cls in module["classes"]:
        print("[CLASS]",cls["name"])
        for method in cls["methods"]:
            print("[METHOD]",method["name"],method["signature"])
assert any(m["imported"] for m in report["modules"]),"NO_EXISTING_SINGLE_WRITER_MODULE_IMPORTABLE"
print("[PASS] CHF-008 exact existing single-writer contract discovery certified")
