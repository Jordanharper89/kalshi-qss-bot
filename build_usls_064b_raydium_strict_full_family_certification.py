from pathlib import Path

ROOT = Path(__file__).resolve().parent
SUB = ROOT / "qseries_v2/oracle_strategy_intelligence/solana_universal_trade_tape"
MOD = SUB / "usls_064b_raydium_strict_full_family_certification.py"
TEST = ROOT / "test_usls_064b_raydium_strict_full_family_certification.py"

MOD_TEXT = r'''from __future__ import annotations
import json
from pathlib import Path

def build(root):
    base=Path(root)/"runtime_state/solana_opportunities/universal_trade_tape"
    prior=json.loads((base/"raydium_full_family_final_gate.json").read_text(encoding="utf-8"))
    ll=json.loads((base/"launchlab_universal_trade_rows.json").read_text(encoding="utf-8"))

    matrix=dict(prior["matrix"])
    matrix["RAYDIUM_LAUNCHLAB"]={
        **matrix["RAYDIUM_LAUNCHLAB"],
        "exact_universal_trade_rows":ll["exact_trade_count"],
        "status":"EXACT_LAUNCHLAB_BUY_TRADE_DECODER_CERTIFIED"
        if ll["exact_trade_count"]>=4 else "NOT_CERTIFIED"
    }

    strict=(
        matrix["RAYDIUM_V4"]["status"]=="EXACT_QUOTE_ORIENTED_TRADE_DECODER_CERTIFIED"
        and matrix["RAYDIUM_CPMM"]["status"]=="EXACT_QUOTE_ORIENTED_TRADE_DECODER_CERTIFIED"
        and matrix["RAYDIUM_CLMM"]["status"]=="EXACT_QUOTE_ORIENTED_TRADE_DECODER_CERTIFIED"
        and matrix["RAYDIUM_LAUNCHLAB"]["status"]=="EXACT_LAUNCHLAB_BUY_TRADE_DECODER_CERTIFIED"
    )

    return {
        "revision":"USLS_064B",
        "matrix":matrix,
        "strict_raydium_family_certified":strict,
        "raydium_family_boundary_closed":strict,
        "phase4_status":"IN_PROGRESS",
        "next_boundary":"METEORA_ORCA_SHARED_DECODER_PLUGINS"
        if strict else "CONTINUE_RAYDIUM_REPAIR",
        "profitability_claimed":False,
        "execution_authority":False,
        "read_only":True
    }

def write(root):
    d=build(root)
    p=Path(root)/"runtime_state/solana_opportunities/universal_trade_tape/raydium_strict_full_family_certification.json"
    p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8")
    return p,d
'''

TEST_TEXT = r'''import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_064b_raydium_strict_full_family_certification import write

ROOT=Path(__file__).resolve().parent

class T(unittest.TestCase):
    def test_final(self):
        p,d=write(ROOT)
        print("[STATE]",json.dumps({
            "strict_raydium_family_certified":d["strict_raydium_family_certified"],
            "raydium_family_boundary_closed":d["raydium_family_boundary_closed"],
            "phase4_status":d["phase4_status"],
            "next_boundary":d["next_boundary"]
        },sort_keys=True))

        for venue,state in d["matrix"].items():
            print("[RAYDIUM]",venue,json.dumps(state,sort_keys=True))

        self.assertTrue(d["strict_raydium_family_certified"],"RAYDIUM_FAMILY_NOT_STRICTLY_COMPLETE")
        self.assertTrue(d["raydium_family_boundary_closed"])
        self.assertEqual(d["next_boundary"],"METEORA_ORCA_SHARED_DECODER_PLUGINS")
        self.assertFalse(d["profitability_claimed"])
        self.assertFalse(d["execution_authority"])

        print("[PASS] USLS-064B strict Raydium full-family certification")
        print("[PASS] V4 + CPMM + CLMM + LaunchLab physically closed")
        print("[NEXT] METEORA_ORCA_SHARED_DECODER_PLUGINS")
        print("[PASS] execution_authority=FALSE")

if __name__=="__main__":
    unittest.main()
'''

SUB.mkdir(parents=True,exist_ok=True)
MOD.write_text(MOD_TEXT,encoding="utf-8")
TEST.write_text(TEST_TEXT,encoding="utf-8")
print("[PASS] installed:",MOD.relative_to(ROOT))
print("[PASS] test:",TEST.name)
print("[PASS] execution_authority=FALSE")