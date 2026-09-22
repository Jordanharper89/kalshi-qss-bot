from pathlib import Path

ROOT = Path(__file__).resolve().parent
SUB = ROOT / "qseries_v2/oracle_strategy_intelligence/solana_universal_trade_tape"
MOD = SUB / "usls_063b_launchlab_universal_trade_normalizer.py"
TEST = ROOT / "test_usls_063b_launchlab_universal_trade_normalizer.py"

MOD_TEXT = r'''from __future__ import annotations
import json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_060_launchlab_official_trade_contract import PROGRAM

def build(root):
    base=Path(root)/"runtime_state/solana_opportunities/universal_trade_tape"
    src=json.loads((base/"launchlab_exact_account_economics.json").read_text(encoding="utf-8"))
    rows=[]
    for n,x in enumerate(src["rows"]):
        if x["decoder_state"]!="EXACT_LAUNCHLAB_BUY_ECONOMICS":
            continue
        rows.append({
            "trade_id":f'RAYDIUM_LAUNCHLAB:{x["signature"]}:{n}',
            "signature":x["signature"],
            "venue":"RAYDIUM_LAUNCHLAB",
            "program_id":PROGRAM,
            "market_address":x["pool"],
            "token_address":x["base_mint"],
            "quote_mint":x["quote_mint"],
            "side":"BUY",
            "trader":x["trader"],
            "base_amount":x["base_amount"],
            "quote_amount":x["quote_amount"],
            "effective_price":x["effective_price"],
            "decoder_state":"EXACT_ECONOMIC_TRADE",
            "source_lineage":{
                "contract":"USLS_060",
                "census":"USLS_061",
                "economics":"USLS_062C"
            },
            "execution_authority":False
        })
    return {
        "revision":"USLS_063B",
        "exact_trade_count":len(rows),
        "rows":rows,
        "profitability_claimed":False,
        "execution_authority":False,
        "read_only":True
    }

def write(root):
    d=build(root)
    p=Path(root)/"runtime_state/solana_opportunities/universal_trade_tape/launchlab_universal_trade_rows.json"
    p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8")
    return p,d
'''

TEST_TEXT = r'''import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_063b_launchlab_universal_trade_normalizer import write

ROOT=Path(__file__).resolve().parent

class T(unittest.TestCase):
    def test_norm(self):
        p,d=write(ROOT)
        print("[STATE]",json.dumps({
            "exact_trade_count":d["exact_trade_count"],
            "revision":d["revision"]
        },sort_keys=True))
        for x in d["rows"]:
            print("[TRADE]",json.dumps(x,sort_keys=True))
        self.assertEqual(d["exact_trade_count"],4)
        self.assertTrue(all(x["side"]=="BUY" and x["effective_price"]>0 for x in d["rows"]))
        self.assertTrue(all(x["source_lineage"]["economics"]=="USLS_062C" for x in d["rows"]))
        self.assertFalse(d["profitability_claimed"])
        self.assertFalse(d["execution_authority"])
        print("[PASS] USLS-063B four exact LaunchLab trades normalized into universal trade tape")
        print("[PASS] lineage anchored to USLS-062C")
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