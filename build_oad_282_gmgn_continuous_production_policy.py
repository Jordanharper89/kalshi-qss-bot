from __future__ import annotations
import ast, os, textwrap
from pathlib import Path

REVISION="OAD_282_GMGN_CONTINUOUS_PRODUCTION_POLICY_V1"

MODULE_SOURCE=r"""
from __future__ import annotations
from dataclasses import dataclass

READ_ONLY=True
PROBABILITY_ENABLED=False
DIRECTION_ENABLED=False
PUBLICATION_ALLOWED=False
EXECUTION_AUTHORITY=False

@dataclass(frozen=True, slots=True)
class GMGNContinuousPolicy:
    cadence_seconds:float=60.0
    acquisition_timeout_seconds:float=30.0
    persistence_timeout_seconds:float=120.0
    initial_backoff_seconds:float=5.0
    max_backoff_seconds:float=60.0
    checkpoint_every_cycles:int=1
    execution_authority:bool=False

def default_gmgn_continuous_policy():
    return GMGNContinuousPolicy()

def verify_gmgn_continuous_policy(policy=None):
    p=policy or default_gmgn_continuous_policy()
    return (
        p.cadence_seconds>0
        and p.acquisition_timeout_seconds>0
        and p.persistence_timeout_seconds>0
        and p.initial_backoff_seconds>0
        and p.max_backoff_seconds>=p.initial_backoff_seconds
        and p.checkpoint_every_cycles>=1
        and p.execution_authority is False
        and PROBABILITY_ENABLED is False
        and DIRECTION_ENABLED is False
        and PUBLICATION_ALLOWED is False
        and EXECUTION_AUTHORITY is False
    )
"""

TEST_SOURCE=r"""
import unittest
from qseries_v2.oracle_adapters.independent.oad_282_gmgn_continuous_production_policy import *

class T(unittest.TestCase):
    def test_policy(self):
        p=default_gmgn_continuous_policy()
        self.assertTrue(verify_gmgn_continuous_policy(p))
        self.assertEqual(p.cadence_seconds,60.0)
        self.assertFalse(p.execution_authority)

if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-282 GMGN continuous production policy certified")
"""

def root():
    from pathlib import Path
    for b in (Path.cwd().resolve(), Path(__file__).resolve().parent):
        for p in (b, *b.parents):
            if (p/"qseries_v2").is_dir():
                return p
    raise RuntimeError("Q Series repository root not found")

def write_checked(path, source):
    s=textwrap.dedent(source).lstrip()
    ast.parse(s, filename=str(path))
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(s,encoding="utf-8",newline="\n")
    os.replace(tmp,path)

def main():
    r=root()
    dep=r/"qseries_v2/oracle_adapters/independent/oad_281_gmgn_solana_single_writer_postgresql_persistence.py"
    if not dep.is_file(): raise RuntimeError("certified OAD-281 missing")
    if "persist_gmgn_solana_token_intelligence" not in dep.read_text(encoding="utf-8"):
        raise RuntimeError("exact OAD-281 persistence symbol missing")
    mod=r/"qseries_v2/oracle_adapters/independent/oad_282_gmgn_continuous_production_policy.py"
    test=r/"test_oad_282_gmgn_continuous_production_policy.py"
    write_checked(mod,MODULE_SOURCE); write_checked(test,TEST_SOURCE)
    print("[PASS] exact OAD-281 persistence boundary verified")
    print("[PASS] OAD-282 module installed")
    print("[PASS] probability=FALSE direction=FALSE publication=FALSE execution=FALSE")
    print("[DONE] OAD-282 INSTALLATION COMPLETE")
if __name__=="__main__": main()
