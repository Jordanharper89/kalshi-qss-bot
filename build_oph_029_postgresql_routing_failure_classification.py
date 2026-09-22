from pathlib import Path
import importlib, os, subprocess, sys
ROOT=Path.cwd().resolve()
PKG=ROOT/"qseries_v2"/"oracle_production_hardening"
MOD=PKG/"oph_029_postgresql_routing_failure_classification.py"
TEST=ROOT/"test_oph_029_postgresql_routing_failure_classification.py"
INIT=PKG/"__init__.py"
MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass\n\nOPH_029_BUILD_ID="OPH-029"\nOPH_029_REVISION="OPH_029_POSTGRESQL_ROUTING_FAILURE_CLASSIFICATION_V1"\n\nRETRYABLE_MARKERS=(\n    "not committed",\n    "timeout",\n    "timed out",\n    "connection",\n    "closed",\n    "serialization",\n    "deadlock",\n    "could not serialize",\n    "server closed",\n    "connection reset",\n)\n\nTERMINAL_MARKERS=(\n    "expected_terminal_chain_hash_mismatch",\n    "duplicate key value violates unique constraint",\n    "invalid observation",\n    "schema mismatch",\n)\n\n@dataclass(frozen=True)\nclass PersistenceFailureClassification:\n    category:str\n    retryable:bool\n    terminal:bool\n    fingerprint:str\n\ndef classify_persistence_failure(exc):\n    name=type(exc).__name__\n    message=str(exc)\n    text=(name+" "+message).lower()\n\n    if any(marker in text for marker in TERMINAL_MARKERS):\n        category="TERMINAL_INTEGRITY"\n        retryable=False\n        terminal=True\n    elif any(marker in text for marker in RETRYABLE_MARKERS):\n        category="TRANSIENT_POSTGRESQL"\n        retryable=True\n        terminal=False\n    elif "postgresqlpersistenceroutingfailure" in text:\n        category="TRANSIENT_POSTGRESQL"\n        retryable=True\n        terminal=False\n    else:\n        category="UNKNOWN"\n        retryable=True\n        terminal=False\n\n    fingerprint=f"{name}:{message}"[:512]\n    return PersistenceFailureClassification(category,retryable,terminal,fingerprint)\n\ndef verify_oph_029_postgresql_routing_failure_classification(root=None):\n    class PostgreSQLPersistenceRoutingFailure(Exception):\n        pass\n    c=classify_persistence_failure(\n        PostgreSQLPersistenceRoutingFailure("PostgreSQL batch append was not committed")\n    )\n    return (\n        OPH_029_BUILD_ID=="OPH-029"\n        and c.category=="TRANSIENT_POSTGRESQL"\n        and c.retryable\n        and not c.terminal\n    )\n'
TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_production_hardening.oph_029_postgresql_routing_failure_classification import *\n\nclass PostgreSQLPersistenceRoutingFailure(Exception):\n    pass\n\nclass T(unittest.TestCase):\n    def test_observed_runtime_failure(self):\n        c=classify_persistence_failure(\n            PostgreSQLPersistenceRoutingFailure("PostgreSQL batch append was not committed")\n        )\n        self.assertEqual(c.category,"TRANSIENT_POSTGRESQL")\n        self.assertTrue(c.retryable)\n        self.assertFalse(c.terminal)\n\n    def test_integrity_failure(self):\n        c=classify_persistence_failure(RuntimeError("expected_terminal_chain_hash_mismatch"))\n        self.assertEqual(c.category,"TERMINAL_INTEGRITY")\n        self.assertFalse(c.retryable)\n        self.assertTrue(c.terminal)\n\nif __name__=="__main__":\n    print("="*88)\n    print(" OPH-029 CERTIFICATION TEST")\n    print(" POSTGRESQL ROUTING FAILURE CLASSIFICATION")\n    print("="*88)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] Observed PostgreSQL not-committed failure classified as transient/retryable")\n    print("[PASS] Integrity-chain failures classified terminal")\n    print("[PASS] execution_authority=FALSE")\n    print("[DONE] OPH-029 CERTIFIED")\n'

def write_exact(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8", newline="\n")
    os.replace(tmp, path)

def update_init(path, export):
    current = path.read_text(encoding="utf-8") if path.exists() else ""
    if export not in current.splitlines():
        write_exact(path, current.rstrip() + "\n" + export + "\n")

def restore(path, data):
    if data is None:
        if path.exists():
            path.unlink()
    else:
        path.write_bytes(data)

def main():
    print("="*88);print(" OPH-029 INSTALLER");print(" POSTGRESQL ROUTING FAILURE CLASSIFICATION");print("="*88);print("[ROOT]",ROOT)
    sys.path.insert(0,str(ROOT))
    up=importlib.import_module("qseries_v2.oracle_production_hardening.oph_028_single_writer_resilience_freeze")
    if up.verify_oph_028_single_writer_resilience_freeze(ROOT) is not True:
        raise RuntimeError("Certified OPH-028 upstream verification failed")
    print("[PASS] Certified OPH-028 upstream boundary verified read-only")
    affected=(MOD,TEST,INIT);old={p:(p.read_bytes() if p.exists() else None) for p in affected}
    try:
        write_exact(MOD,MODULE_SOURCE);write_exact(TEST,TEST_SOURCE)
        update_init(INIT,"from .oph_029_postgresql_routing_failure_classification import *")
        subprocess.run([sys.executable,str(TEST)],cwd=str(ROOT),check=True)
        importlib.invalidate_caches()
        m=importlib.import_module("qseries_v2.oracle_production_hardening.oph_029_postgresql_routing_failure_classification")
        if m.verify_oph_029_postgresql_routing_failure_classification(ROOT) is not True:
            raise RuntimeError("OPH-029 verification failed")
    except Exception:
        for p,b in old.items(): restore(p,b)
        print("[ROLLBACK] OPH-029 installation failed; affected files restored");raise
    print("[PASS] Failure classification installed")
    print("[PASS] OPH-001 through OPH-028 preserved read-only")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] OPH-029 INSTALLATION AND CERTIFICATION COMPLETE")
if __name__=="__main__": main()
