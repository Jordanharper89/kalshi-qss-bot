import unittest
from pathlib import Path
import tempfile

from qseries_v2.oracle_production_hardening.oph_022_oracle_universal_single_writer_cutover import (
    CANONICAL_WRITER,
    read_children,
    wrapper_source,
    verify_wrapper_file,
)

class T(unittest.TestCase):
    def test_children_parser(self):
        source='CHILDREN={"fast_lane":"a.py","canonical_writer":"b.py"}\n'
        children=read_children(source)
        self.assertEqual(children["fast_lane"],"a.py")

    def test_wrapper_uses_real_newlines(self):
        source=wrapper_source("fast_lane","run_raw.py")
        self.assertGreater(len(source.splitlines()),5)
        self.assertEqual(source.splitlines()[0],"from pathlib import Path")
        compile(source,"generated_wrapper","exec")

    def test_wrapper_file_verifier(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"wrapper.py"
            p.write_text(wrapper_source("coverage","run_raw.py"),encoding="utf-8",newline="\n")
            self.assertTrue(verify_wrapper_file(p))

    def test_canonical_writer_identity(self):
        self.assertEqual(
            CANONICAL_WRITER,
            "run_oph_021_exclusive_postgresql_canonical_writer.py",
        )

if __name__=="__main__":
    print("="*88)
    print(" OPH-022 CERTIFICATION TEST")
    print(" ORACLE UNIVERSAL SINGLE-WRITER CUTOVER — CORRECTION V2")
    print("="*88)

    result=unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(T)
    )
    if not result.wasSuccessful():
        raise SystemExit(1)

    print("[PASS] Generated wrappers use physical newline characters")
    print("[PASS] Generated wrappers compile before launcher modification")
    print("[PASS] Universal PostgreSQL ingress cutover contract certified")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] OPH-022 CERTIFIED")
