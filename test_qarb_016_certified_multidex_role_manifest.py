
import json,tempfile,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot.certified_roles import *
class T(unittest.TestCase):
    def test_certified_role_load(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"runtime_state/x";p.mkdir(parents=True)
            (p/"raydium_exact_instruction_pool_role_decoder.json").write_text(json.dumps({
              "rows":[{"venue":"RAYDIUM_CLMM","pool":"P"*32,"mint_a":"A"*32,"mint_b":"B"*32,
                       "accounts":{"vault_a":"V"*32,"vault_b":"W"*32,"tick_array":"T"*32}}]}),encoding="utf-8")
            rows=load(td);self.assertEqual(len(rows),1);self.assertEqual(len(rows[0].accounts),3)
        print("[PASS] certified role artifacts -> exact watched-account manifest")
if __name__=="__main__": unittest.main(verbosity=2)
