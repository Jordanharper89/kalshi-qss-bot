import base64,unittest
from qseries_v2.oracle_strategy_intelligence.solana_money.atomic_crossdex_sim import core as c
SYS="11111111111111111111111111111111"
PAYER="4Nd1mY6wS6V6L1tUQ2gD7BzS7PnXfVh3N4BfJkM9fQ3M"
class T(unittest.TestCase):
 def test_b58_system(self):
  self.assertEqual(c.b58decode(SYS),b"\0"*32);print("[PASS] base58 pubkey decode")
 def test_cleanup_deferred(self):
  x={"setupInstructions":[],"otherInstructions":[],"swapInstruction":{"programId":SYS,"accounts":[],"data":""},
     "cleanupInstruction":{"programId":SYS,"accounts":[],"data":base64.b64encode(b"A").decode()}}
  y={"setupInstructions":[],"otherInstructions":[],"swapInstruction":{"programId":SYS,"accounts":[],"data":base64.b64encode(b"B").decode()},
     "cleanupInstruction":{"programId":SYS,"accounts":[],"data":base64.b64encode(b"C").decode()}}
  z=c.compose_instruction_json(x,y)
  self.assertEqual(base64.b64decode(z[-2]["data"]),b"C");self.assertEqual(base64.b64decode(z[-1]["data"]),b"A")
  print("[PASS] both swap legs precede wrapped-SOL cleanup")
 def test_sim_pnl_parser_contract(self):
  old=c.rpc
  c.rpc=lambda m,p:{"err":None,"fee":5000,"unitsConsumed":333000,"preBalances":[1000000000],"postBalances":[1002500000],"logs":[]}
  try:
   x=c.simulate(PAYER,b"x");self.assertEqual(x["pnl_lamports"],2500000);self.assertEqual(x["fee_lamports"],5000)
  finally:c.rpc=old
  print("[PASS] simulation payer balance delta becomes PNL")
 def test_failed_sim_not_profit(self):
  old=c.rpc
  c.rpc=lambda m,p:{"err":{"InstructionError":[1,"Custom"]},"fee":5000,"unitsConsumed":100,"preBalances":[10],"postBalances":[5],"logs":[]}
  try:
   x=c.simulate(PAYER,b"x");self.assertIsNotNone(x["err"]);self.assertLess(x["pnl_lamports"],0)
  finally:c.rpc=old
  print("[PASS] failed atomic simulation cannot masquerade as profit")
if __name__=="__main__":unittest.main(verbosity=2)
