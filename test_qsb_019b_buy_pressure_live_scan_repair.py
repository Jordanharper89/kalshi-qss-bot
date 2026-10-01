
import json,tempfile,time,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_money.qsb_019b_buy_pressure_live_scan_repair import (
    fresh_candidate_files,load_tail_objects,EXECUTION_AUTHORITY,PAPER_ONLY
)

class T(unittest.TestCase):
    def test_bounded_recent_scan(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            base=root/"runtime_state/solana_opportunities"
            base.mkdir(parents=True)
            for i in range(5):
                p=base/f"{i}.json"
                p.write_text(json.dumps({"i":i}),encoding="utf-8")
            files=fresh_candidate_files(root,max_files=3,max_age_seconds=7200)
            self.assertEqual(len(files),3)

    def test_tail_jsonl(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"x.jsonl"
            p.write_text("\n".join(json.dumps({"i":i}) for i in range(1000)),encoding="utf-8")
            rows=load_tail_objects(p,max_lines=25)
            self.assertEqual(len(rows),25)
            self.assertEqual(rows[-1]["i"],999)

    def test_authority(self):
        self.assertFalse(EXECUTION_AUTHORITY)
        self.assertTrue(PAPER_ONLY)

if __name__=="__main__":
    unittest.main(verbosity=2)
