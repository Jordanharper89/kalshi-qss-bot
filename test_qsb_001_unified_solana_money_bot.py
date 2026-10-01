import json,os,tempfile,time,unittest
from pathlib import Path
from qseries_v2.solana_money_bot import UnifiedSolanaMoneyBot

class T(unittest.TestCase):
 def test_unified_paper_path(self):
  old=os.environ.get("QSB_MIN_SCORE");os.environ["QSB_MIN_SCORE"]="0.45"
  try:
   with tempfile.TemporaryDirectory() as td:
    root=Path(td);p=root/"runtime_state/solana_opportunities/synthetic.json"
    p.parent.mkdir(parents=True,exist_ok=True);t=time.time()-40
    prices=[1.00,1.16,1.31,1.42,1.18,0.99,1.00,1.01,1.09,1.15]
    rows=[]
    for i,px in enumerate(prices):
     rows.append({"market_address":"POOL1","family":"PUMP_SWAP","token_mint":"TokenMint111",
      "last_price":px,"observed_unix":t+i*4,"volume":100+i*15,"buy_count":12+i,"sell_count":10})
    p.write_text(json.dumps({"rows":rows}),encoding="utf-8")
    b=UnifiedSolanaMoneyBot(root);d=b.cycle()
    print("[STATE]",json.dumps({"candidates":len(d["candidates"]),"action":d["action"]["action"],
      "oracle_required_for_decision":d["oracle_required_for_decision"]},sort_keys=True))
    self.assertGreaterEqual(len(d["candidates"]),1)
    self.assertEqual(d["action"]["action"],"PAPER_ENTER")
    self.assertFalse(d["oracle_required_for_decision"])
    self.assertFalse(d["live_armed"])
    self.assertTrue((root/"runtime_state/qseries/solana_money_bot/positions.json").exists())
    print("[PASS] QSB-001 unified detect->score->paper-execute path")
  finally:
   if old is None:os.environ.pop("QSB_MIN_SCORE",None)
   else:os.environ["QSB_MIN_SCORE"]=old

if __name__=="__main__":
 unittest.main()
