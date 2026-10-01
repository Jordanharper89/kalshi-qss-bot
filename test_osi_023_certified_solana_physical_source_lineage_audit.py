import json
import unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_intelligence.osi_023_certified_solana_physical_source_lineage_audit import audit, write_report

ROOT = Path(__file__).resolve().parent
TARGETS = ['qseries_v2/oracle_adapters/independent/oad_273_solana_pinned_pool_live_snapshot_persistence.py', 'qseries_v2/oracle_adapters/independent/oad_274_solana_multi_horizon_condition_windows.py', 'qseries_v2/oracle_adapters/independent/oad_275_solana_continuous_observation_resilient_worker.py', 'qseries_v2/oracle_adapters/independent/oad_312_solana_continuous_temporal_history_activation_gate.py', 'qseries_v2/oracle_adapters/independent/oad_314_solana_verified_forward_outcome_attribution.py', 'qseries_v2/oracle_adapters/independent/oad_360_solana_exact_observation_readback.py', 'qseries_v2/oracle_adapters/independent/oad_372_solana_final_persistence_continuity.py']

class T(unittest.TestCase):
    def test_physical(self):
        result = audit(ROOT, TARGETS)
        report = write_report(ROOT, TARGETS)
        self.assertTrue(report.is_file())
        self.assertGreater(result["existing_source_count"], 0)
        self.assertFalse(result["execution_authority"])
        print("[REPORT]", report)
        print("[CERTIFIED_MODULES_FOUND]", result["existing_source_count"])
        print("[RUNTIME_INVENTORY_COUNT]", len(result["runtime_inventory"]))
        for src in result["source_modules"]:
            if src["exists"]:
                print("[SOURCE]", src["path"], "matches=", len(src["matches"]))
        if result["runtime_inventory"]:
            print("[TOP_RUNTIME_FILE]", json.dumps(result["runtime_inventory"][0], sort_keys=True))
        print("[PASS] OSI-023 certified Solana physical source lineage audit")
        print("[TRADER] Locates the real Solana tape already produced by certified Oracle pavement")
        print("[PASS] execution_authority=FALSE")
        print("[SCOPE] Read-only lineage audit; no new feed and no source mutation")

if __name__ == "__main__":
    unittest.main()
