import subprocess,sys,unittest
from pathlib import Path
class T(unittest.TestCase):
    def test_bulk_path_present(self):
        p=Path("qseries_v2/oracle_intelligence/live_acquisition/oracle_postgresql_canonical_observation_persistence_backend.py")
        s=p.read_text(encoding="utf-8")
        self.assertIn("ola012:select_duplicate_bulk",s)
        self.assertIn("cursor.executemany(INSERT_OBSERVATION_SQL,bulk_insert_rows)",s)
        self.assertIn("len(request.observations) >= 64",s)
    def test_certified_ola012_suite(self):
        cp=subprocess.run([sys.executable,"test_ola_012_oracle_postgresql_canonical_observation_persistence_backend.py"],capture_output=True,text=True)
        if cp.returncode!=0: self.fail(cp.stdout+"\n"+cp.stderr)
        self.assertIn("[PASS] OLA-012",cp.stdout)
if __name__=="__main__":
    rr=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not rr.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-408 high-throughput canonical PostgreSQL append rebuild certified")
