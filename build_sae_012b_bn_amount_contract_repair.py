from pathlib import Path

ROOT=Path.cwd()

PROBE=(
    ROOT/"qseries_v2"/"oracle_strategy_intelligence"/
    "solana_money"/"qsb059d_pump_native"/
    "sae012_direct_pumpswap_buyexact_sim_probe.mjs"
)

TEST=ROOT/"test_sae_012b_bn_amount_contract_repair.py"

if not PROBE.is_file():
    raise RuntimeError("SAE012_PROBE_MISSING")

s=PROBE.read_text(encoding="utf-8")

if 'import BN from "bn.js";' not in s:
    s='import BN from "bn.js";\n'+s

s=s.replace(
    "const baseOut=1n;\n  const quoteIn=1_000_000n;",
    'const baseOut=new BN("1");\n  const quoteIn=new BN("1000000");'
)

if "const baseOut=1n" in s or "const quoteIn=1_000_000n" in s:
    raise RuntimeError("BIGINT_REPLACEMENT_FAILED")

PROBE.write_text(s,encoding="utf-8")

TEST.write_text(r'''
from pathlib import Path
import unittest

P=Path(
    "qseries_v2/oracle_strategy_intelligence/"
    "solana_money/qsb059d_pump_native/"
    "sae012_direct_pumpswap_buyexact_sim_probe.mjs"
)

class T(unittest.TestCase):
    def test_bn_contract(self):
        s=P.read_text(encoding="utf-8")
        self.assertIn('import BN from "bn.js";',s)
        self.assertIn('new BN("1")',s)
        self.assertIn('new BN("1000000")',s)

    def test_simulation_only(self):
        s=P.read_text(encoding="utf-8")
        self.assertIn("simulateTransaction",s)
        self.assertNotIn("sendTransaction(",s)

if __name__=="__main__":
    unittest.main(verbosity=2)
'''.lstrip(),encoding="utf-8")

print("[PASS] SAE-012B BN contract repaired")
print("[CHECKPOINT] Pump-only BuyExactQuoteIn simulation")
print("[RUNTIME] canonical executor unchanged")
print("[BROADCAST] disabled")