import tempfile,time,unittest
from qseries_v2.oracle_strategy_intelligence.solana_money.mriya_route_anatomy.registry import *
from qseries_v2.oracle_strategy_intelligence.solana_money.mriya_route_anatomy.anatomy import analyze_target,reconstruct_legs

TP="TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"
WSOL="So11111111111111111111111111111111111111112"
TOK="Token11111111111111111111111111111111111111"

def fixture(failed=False):
    keys=[
      {"pubkey":TARGET_WALLET,"signer":True},
      {"pubkey":TARGET_EXECUTOR,"signer":False},
      {"pubkey":PROGRAMS["METEORA_DLMM"],"signer":False},
      {"pubkey":PROGRAMS["PUMP_SWAP"],"signer":False},
      {"pubkey":TP,"signer":False},
      {"pubkey":"W_WSOL","signer":False},{"pubkey":"W_TOK","signer":False},
      {"pubkey":"POOL_A","signer":False},{"pubkey":"POOL_B","signer":False},
    ]
    meta={"err":{"InstructionError":[0,"Custom"]} if failed else None,"fee":5000,"computeUnitsConsumed":120000,
      "preBalances":[1000000000]+[0]*8,"postBalances":[1001000000]+[0]*8,
      "preTokenBalances":[
        {"accountIndex":5,"owner":TARGET_WALLET,"mint":WSOL,"uiTokenAmount":{"uiAmountString":"10"}},
        {"accountIndex":6,"owner":TARGET_WALLET,"mint":TOK,"uiTokenAmount":{"uiAmountString":"0"}}],
      "postTokenBalances":[
        {"accountIndex":5,"owner":TARGET_WALLET,"mint":WSOL,"uiTokenAmount":{"uiAmountString":"10.08"}},
        {"accountIndex":6,"owner":TARGET_WALLET,"mint":TOK,"uiTokenAmount":{"uiAmountString":"0"}}],
      "innerInstructions":[{"index":0,"instructions":[
        {"programId":PROGRAMS["METEORA_DLMM"]},
        {"programId":TP,"parsed":{"type":"transferChecked","info":{"source":"W_WSOL","destination":"POOL_A","mint":WSOL,"tokenAmount":{"uiAmountString":"1"}}}},
        {"programId":TP,"parsed":{"type":"transferChecked","info":{"source":"POOL_A","destination":"W_TOK","mint":TOK,"tokenAmount":{"uiAmountString":"100"}}}},
        {"programId":PROGRAMS["PUMP_SWAP"]},
        {"programId":TP,"parsed":{"type":"transferChecked","info":{"source":"W_TOK","destination":"POOL_B","mint":TOK,"tokenAmount":{"uiAmountString":"100"}}}},
        {"programId":TP,"parsed":{"type":"transferChecked","info":{"source":"POOL_B","destination":"W_WSOL","mint":WSOL,"tokenAmount":{"uiAmountString":"1.08"}}}},
      ]}]}
    return {"transaction":{"signatures":["SIG1"],"message":{"accountKeys":keys,"instructions":[{"programId":TARGET_EXECUTOR}]}}, "meta":meta}

class T(unittest.TestCase):
    def test_success_two_leg_exact_anatomy(self):
        a=analyze_target(fixture(False),123,1000)
        self.assertFalse(a["failed"]);self.assertTrue(a["executor_present"]);self.assertEqual(a["leg_count"],2)
        self.assertEqual(a["resolved_legs"],2);self.assertTrue(a["closed_anchor_cycle"])
        self.assertAlmostEqual(a["wallet_anchor_deltas"]["WSOL"],.08,places=9)
        self.assertEqual([x["venue"] for x in a["legs"]],["METEORA_DLMM","PUMP_SWAP"])
        print("[PASS] successful Mriya-style 2-leg route reconstructs exact wallet-owned input/output")

    def test_leg_amounts(self):
        a=analyze_target(fixture(False),123,1000)
        x,y=a["legs"]
        self.assertEqual(x["input_asset"],WSOL);self.assertAlmostEqual(x["input_amount"],1)
        self.assertEqual(x["output_asset"],TOK);self.assertAlmostEqual(x["output_amount"],100)
        self.assertEqual(y["input_asset"],TOK);self.assertAlmostEqual(y["output_amount"],1.08)
        print("[PASS] leg chain carries exact observed transfer amounts and direction")

    def test_failed_transaction_preserves_failure(self):
        a=analyze_target(fixture(True),123,1000)
        self.assertTrue(a["failed"]);self.assertFalse(a["closed_anchor_cycle"]);self.assertIsNotNone(a["error"])
        print("[PASS] failed executor transaction retained for failure anatomy, never mislabeled winner")

    def test_ambiguous_leg_stays_unresolved(self):
        x=fixture(False)
        x["meta"]["innerInstructions"][0]["instructions"].insert(3,
          {"programId":TP,"parsed":{"type":"transferChecked","info":{"source":"POOL_A","destination":"W_WSOL","mint":WSOL,"tokenAmount":{"uiAmountString":"0.01"}}}})
        a=analyze_target(x,123,1000)
        self.assertFalse(a["legs"][0]["resolved"])
        print("[PASS] ambiguous transfer evidence remains UNRESOLVED instead of invented")

    def test_signature_and_fee_compute_preserved(self):
        a=analyze_target(fixture(False),123,1000)
        self.assertEqual(a["signature"],"SIG1");self.assertEqual(a["fee_lamports"],5000);self.assertEqual(a["compute_units"],120000)
        print("[PASS] exact signature, fee and compute evidence preserved")

    def test_distinct_signatures_support_same_slot_without_duplicate_assumption(self):
        a=analyze_target(fixture(False),123,1000);b=fixture(False);b["transaction"]["signatures"]=["SIG2"]
        b=analyze_target(b,123,1000)
        self.assertNotEqual(a["signature"],b["signature"]);self.assertEqual(a["slot"],b["slot"])
        print("[PASS] two Mriya transactions in one slot are distinct by signature, not mistaken duplicates")

    def test_non_target_ignored(self):
        x=fixture(False);x["transaction"]["message"]["accountKeys"][0]["pubkey"]="OTHER"
        self.assertIsNone(analyze_target(x,123,1000))
        print("[PASS] non-target wallet transactions ignored")

if __name__=="__main__":unittest.main(verbosity=2)
