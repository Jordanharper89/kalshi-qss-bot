import json,tempfile,time,unittest
from pathlib import Path
from qseries_v2.solana_money_bot_proof import real_repo_proof

class T(unittest.TestCase):
 def test_truth_gate_against_qsb_001c_contract(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td)
   p=root/"runtime_state/solana_opportunities/physical_feed.json"
   p.parent.mkdir(parents=True,exist_ok=True)
   t=time.time()-25
   prices=[1.00,1.15,1.30,1.42,1.18,1.00,1.01,1.02,1.09,1.16]
   rows=[{"market_address":"REAL-POOL","family":"PUMP_SWAP","token_mint":"REAL-MINT",
          "last_price":px,"observed_unix":t+i*2,"volume":100+i*10,
          "buy_count":15+i,"sell_count":10} for i,px in enumerate(prices)]
   p.write_text(json.dumps({"rows":rows}),encoding="utf-8")

   proof=real_repo_proof(root)
   print("[PROOF]",json.dumps(proof,sort_keys=True))
   self.assertTrue(proof["live_repo_ingestion_proven"])
   self.assertTrue(proof["real_market_path_proven"])
   self.assertTrue(proof["token_identity_proven"])
   self.assertTrue(proof["physical_integration_pass"])
   self.assertFalse(proof["profitability_proven"])
   self.assertTrue((root/"runtime_state/qseries/solana_money_bot/proof.json").exists())
   print("[PASS] QSB-002B compatible with QSB-001C and separates integration proof from profitability proof")

if __name__=="__main__":
 unittest.main()
