import unittest
from qseries_v2.solana_onchain_burst_radar import _mints,WSOL,USDC
class T(unittest.TestCase):
 def test_cpmm_transaction_mint_extraction(self):
  tx={"meta":{"preTokenBalances":[{"mint":WSOL},{"mint":"MEME111"}],
              "postTokenBalances":[{"mint":"MEME111"},{"mint":"MEME222"},{"mint":USDC}]}}
  self.assertEqual(_mints(tx),["MEME111","MEME222"])
  print("[PASS] QSB-010 extracts non-SOL/non-USDC token mints from hydrated on-chain DEX transactions")
if __name__=="__main__":unittest.main()
