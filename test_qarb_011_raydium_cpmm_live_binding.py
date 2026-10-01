
import json,struct,tempfile,unittest
from pathlib import Path
from time import perf_counter_ns
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot.dex.raydium_cpmm_live import *

class T(unittest.TestCase):
    def test_registry_discovery_and_live_update(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"runtime_state/x";p.mkdir(parents=True)
            obj={"rows":[{"venue":"RAYDIUM_CPMM","pool":"P"*32,"mint_a":"A"*32,"mint_b":"B"*32,
                          "vault_a":"V"*32,"vault_b":"W"*32}]}
            (p/"x.json").write_text(json.dumps(obj),encoding="utf-8")
            rows=discover(td);self.assertEqual(len(rows),1)
            def acct(addr):
                raw=bytearray(72);struct.pack_into("<Q",raw,64,1000 if addr=="V"*32 else 2000)
                return bytes(raw),1
            st=hydrate(rows[0],acct)
            raw=bytearray(72);struct.pack_into("<Q",raw,64,1500)
            self.assertTrue(update(st,rows[0],"V"*32,bytes(raw),perf_counter_ns()))
            self.assertEqual(st.reserve_a,1500)
        print("[PASS] Raydium CPMM artifact discovery -> hydrate -> live reserve update")
    def test_local_quote(self):
        d=LivePool("P","A","B","V","W");s=PoolState("P","A","B",1000,2000,25,10000,perf_counter_ns())
        self.assertGreater(quote(s,"A",10),0)
        print("[PASS] Raydium CPMM live state feeds local quote")
if __name__=="__main__": unittest.main(verbosity=2)
