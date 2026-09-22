import json
import tempfile
import unittest
from pathlib import Path

from qseries_v2.oracle_adapters.independent.oad_394_solana_finalized_head_missing_slot_scheduler import (
    build_missing_slot_schedule,
    read_last_committed_slot,
)

class T(unittest.TestCase):
    def test_scheduler(self):
        x=build_missing_slot_schedule(100,110,max_slots=4,skipped_slots=(103,))
        print("[SCHEDULE]",x)
        self.assertEqual(x.scheduled_slots,(101,102,104,105))
        self.assertEqual(x.remaining_lag_slots,5)

        y=build_missing_slot_schedule(110,110,max_slots=4)
        self.assertTrue(y.caught_up)
        self.assertEqual(y.scheduled_slots,())

    def test_checkpoint_discovery_without_hardcoded_module_dependency(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            p=root/"runtime_state"/"solana_universal_chain"/"checkpoint.json"
            p.parent.mkdir(parents=True)
            p.write_text(json.dumps({"generation":9,"last_committed_slot":444147940}),encoding="utf-8")
            self.assertEqual(read_last_committed_slot(root),444147940)

if __name__=="__main__":
    rr=unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(T)
    )
    if not rr.wasSuccessful():
        raise SystemExit(1)

    print("[PASS] OAD-394 finalized-head missing-slot scheduler certified")
    print("[PASS] no guessed OAD-323 module dependency")
