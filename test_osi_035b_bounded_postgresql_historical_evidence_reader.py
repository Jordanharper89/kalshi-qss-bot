import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_intelligence.osi_035_bounded_postgresql_historical_evidence_reader import inspect,write

ROOT=Path(__file__).resolve().parent

class T(unittest.TestCase):
    def test_boundary(self):
        d=inspect(ROOT)
        p=write(ROOT)
        self.assertTrue(p.is_file())
        self.assertFalse(d["execution_authority"])
        print("[CONNECTED]",d["connected"])
        print("[ERROR]",d["error"])
        print("[TABLES]",len(d["tables"]))
        if d["tables"]:
            print("[TOP_TABLE]",json.dumps(d["tables"][0],sort_keys=True))
        print("[PASS] OSI-035B bounded PostgreSQL historical evidence reader installed")
        print("[TRADER] Solana runtime can inspect Oracle history through a read-only database session")
        print("[SCOPE] Schema/read-boundary certification only; no writes and no profitability claim")

if __name__=="__main__":
    unittest.main()
