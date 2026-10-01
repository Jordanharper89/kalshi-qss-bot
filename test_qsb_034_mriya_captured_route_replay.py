import json,tempfile,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_money.mriya_captured_route_replay.replay import captured_targets,replay,KNOWN_SLOTS
from qseries_v2.oracle_strategy_intelligence.solana_money.mriya_route_anatomy.registry import *

TP="TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"
WSOL="So11111111111111111111111111111111111111112"
TOK="Token11111111111111111111111111111111111111"

def tx(sig,failed=False):
    keys=[{"pubkey":TARGET_WALLET,"signer":True},{"pubkey":TARGET_EXECUTOR,"signer":False},
          {"pubkey":PROGRAMS["METEORA_DLMM"],"signer":False},{"pubkey":PROGRAMS["PUMP_SWAP"],"signer":False},
          {"pubkey":TP,"signer":False},{"pubkey":"W_WSOL","signer":False},{"pubkey":"W_TOK","signer":False},
          {"pubkey":"PA","signer":False},{"pubkey":"PB","signer":False}]
    return {"transaction":{"signatures":[sig],"message":{"accountKeys":keys,"instructions":[{"programId":TARGET_EXECUTOR}]}},
      "meta":{"err":{"InstructionError":[0,"Custom"]} if failed else None,"fee":5000,"computeUnitsConsumed":100000,
      "preBalances":[1000000000]+[0]*8,"postBalances":[1001000000]+[0]*8,
      "preTokenBalances":[
        {"accountIndex":5,"owner":TARGET_WALLET,"mint":WSOL,"uiTokenAmount":{"uiAmountString":"10"}},
        {"accountIndex":6,"owner":TARGET_WALLET,"mint":TOK,"uiTokenAmount":{"uiAmountString":"0"}}],
      "postTokenBalances":[
        {"accountIndex":5,"owner":TARGET_WALLET,"mint":WSOL,"uiTokenAmount":{"uiAmountString":"10.08"}},
        {"accountIndex":6,"owner":TARGET_WALLET,"mint":TOK,"uiTokenAmount":{"uiAmountString":"0"}}],
      "innerInstructions":[{"index":0,"instructions":[
        {"programId":PROGRAMS["METEORA_DLMM"]},
        {"programId":TP,"parsed":{"type":"transferChecked","info":{"source":"W_WSOL","destination":"PA","mint":WSOL,"tokenAmount":{"uiAmountString":"1"}}}},
        {"programId":TP,"parsed":{"type":"transferChecked","info":{"source":"PA","destination":"W_TOK","mint":TOK,"tokenAmount":{"uiAmountString":"100"}}}},
        {"programId":PROGRAMS["PUMP_SWAP"]},
        {"programId":TP,"parsed":{"type":"transferChecked","info":{"source":"W_TOK","destination":"PB","mint":TOK,"tokenAmount":{"uiAmountString":"100"}}}},
        {"programId":TP,"parsed":{"type":"transferChecked","info":{"source":"PB","destination":"W_WSOL","mint":WSOL,"tokenAmount":{"uiAmountString":"1.08"}}}},
      ]}]}}

class Fetcher:
    def __init__(self,blocks):self.blocks=blocks;self.rate_limits=0;self.errors=0
    def fetch(self,slot):return self.blocks.get(slot),False

class T(unittest.TestCase):
    def test_reads_qsb032_captured_signatures(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);p=root/"runtime_state/qseries/qsb032_public_rpc_slot_batched_mriya_arb/ledger.json"
            p.parent.mkdir(parents=True);p.write_text(json.dumps({"target_transactions":[{"slot":450205602,"signature":"ABC"}]}))
            xs=captured_targets(root)
            self.assertTrue(any(x["slot"]==450205602 and x["signature"]=="ABC" for x in xs))
        print("[PASS] QSB-032 captured Mriya signatures are replay input")

    def test_known_session_slots_are_seeded(self):
        with tempfile.TemporaryDirectory() as td:
            xs=captured_targets(Path(td))
            self.assertTrue(all(any(x["slot"]==s for x in xs) for s in KNOWN_SLOTS))
        print("[PASS] known captured slots from live session are never lost")

    def test_replays_success_and_failure_without_waiting(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            p=root/"runtime_state/qseries/qsb032_public_rpc_slot_batched_mriya_arb/ledger.json"
            p.parent.mkdir(parents=True);p.write_text(json.dumps({"target_transactions":[
              {"slot":450205602,"signature":"WIN1"},{"slot":450205602,"signature":"FAIL1"}]}))
            f=Fetcher({450205602:{"blockTime":1000,"transactions":[tx("WIN1",False),tx("FAIL1",True)]}})
            r=replay(root,f)
            got={x["signature"]:x for x in r["routes"]}
            self.assertIn("WIN1",got);self.assertIn("FAIL1",got)
            self.assertFalse(got["WIN1"]["failed"]);self.assertTrue(got["FAIL1"]["failed"])
        print("[PASS] captured win/fail pair is dissected immediately from historical block")

    def test_signature_filter_prevents_same_slot_noise(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);p=root/"runtime_state/qseries/qsb032_public_rpc_slot_batched_mriya_arb/ledger.json"
            p.parent.mkdir(parents=True);p.write_text(json.dumps({"target_transactions":[{"slot":450205602,"signature":"KEEP"}]}))
            f=Fetcher({450205602:{"blockTime":1000,"transactions":[tx("KEEP"),tx("DROP")]}})
            r=replay(root,f);self.assertEqual([x["signature"] for x in r["routes"]],["KEEP"])
        print("[PASS] duplicate same-slot target noise is controlled by exact signature filter")

    def test_report_persists(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);f=Fetcher({})
            replay(root,f)
            self.assertTrue((root/"runtime_state/qseries/qsb034_mriya_captured_route_replay/report.json").is_file())
        print("[PASS] route anatomy replay report persists restart-safe")

if __name__=="__main__":unittest.main(verbosity=2)
