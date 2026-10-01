import unittest,collections
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_intelligence.osi_045_exact_solana_gmgn_postgresql_reader import read

ROOT=Path(__file__).resolve().parent

class T(unittest.TestCase):
    def test_physical(self):
        d=read(ROOT,500)
        self.assertFalse(d["execution_authority"])
        self.assertGreater(d["row_count"],0)
        c=collections.Counter(x["observation_type"] for x in d["rows"])
        print("[ROWS]",d["row_count"])
        print("[TYPES]",dict(c))
        print("[TOP_SOURCE]",d["rows"][0]["source_id"])
        print("[TOP_TYPE]",d["rows"][0]["observation_type"])
        bad=[x for x in d["rows"] if "bitcoin" in x["source_id"].lower() or "mempool" in x["source_id"].lower()]
        self.assertEqual(bad,[])
        print("[PASS] OSI-045B exact Solana/GMGN PostgreSQL reader")
        print("[TRADER] Reads only native Solana, GMGN, and Solana-context warehouse rows")
        print("[PASS] execution_authority=FALSE")

if __name__=="__main__":
    unittest.main()
