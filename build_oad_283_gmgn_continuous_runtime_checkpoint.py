from __future__ import annotations
import ast, os, textwrap
from pathlib import Path

MODULE_SOURCE=r"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
import json, os

READ_ONLY=True
PROBABILITY_ENABLED=False
DIRECTION_ENABLED=False
PUBLICATION_ALLOWED=False
EXECUTION_AUTHORITY=False

@dataclass(frozen=True, slots=True)
class GMGNRuntimeCheckpoint:
    cycles:int
    successes:int
    failures:int
    last_success_at:str|None
    last_error:str|None
    last_token_address:str|None
    last_observation_ids:tuple
    execution_authority:bool=False

def genesis_gmgn_runtime_checkpoint():
    return GMGNRuntimeCheckpoint(0,0,0,None,None,None,(),False)

def checkpoint_path(root=None):
    r=Path(root or Path.cwd()).resolve()
    p=r/"runtime_state"
    p.mkdir(parents=True,exist_ok=True)
    return p/"oad_283_gmgn_continuous_runtime_checkpoint.json"

def load_gmgn_runtime_checkpoint(root=None):
    p=checkpoint_path(root)
    if not p.exists(): return genesis_gmgn_runtime_checkpoint()
    d=json.loads(p.read_text(encoding="utf-8"))
    return GMGNRuntimeCheckpoint(
        int(d["cycles"]),int(d["successes"]),int(d["failures"]),
        d.get("last_success_at"),d.get("last_error"),d.get("last_token_address"),
        tuple(d.get("last_observation_ids") or ()),False
    )

def save_gmgn_runtime_checkpoint(cp,root=None):
    if cp.execution_authority is not False: raise RuntimeError("execution boundary violation")
    p=checkpoint_path(root)
    d=asdict(cp); d["last_observation_ids"]=list(cp.last_observation_ids)
    tmp=p.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(d,sort_keys=True,indent=2)+"\n",encoding="utf-8",newline="\n")
    os.replace(tmp,p)
    return p

def advance_success(cp,token_address,observation_ids):
    return GMGNRuntimeCheckpoint(
        cp.cycles+1,cp.successes+1,cp.failures,
        datetime.now(timezone.utc).isoformat(),None,str(token_address),
        tuple(observation_ids),False
    )

def advance_failure(cp,error):
    return GMGNRuntimeCheckpoint(
        cp.cycles+1,cp.successes,cp.failures+1,
        cp.last_success_at,str(error)[:500],cp.last_token_address,
        cp.last_observation_ids,False
    )
"""

TEST_SOURCE=r"""
import tempfile,unittest
from pathlib import Path
from qseries_v2.oracle_adapters.independent.oad_283_gmgn_continuous_runtime_checkpoint import *

class T(unittest.TestCase):
    def test_roundtrip(self):
        with tempfile.TemporaryDirectory() as d:
            cp=advance_success(genesis_gmgn_runtime_checkpoint(),"TOKEN",("a","b","c"))
            save_gmgn_runtime_checkpoint(cp,d)
            q=load_gmgn_runtime_checkpoint(d)
            self.assertEqual(q.cycles,1); self.assertEqual(q.successes,1)
            self.assertEqual(q.last_token_address,"TOKEN")
            self.assertEqual(q.last_observation_ids,("a","b","c"))
            self.assertFalse(q.execution_authority)

if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-283 durable GMGN checkpoint certified")
"""

def root():
    from pathlib import Path
    for b in (Path.cwd().resolve(), Path(__file__).resolve().parent):
        for p in (b, *b.parents):
            if (p/"qseries_v2").is_dir():
                return p
    raise RuntimeError("Q Series repository root not found")

def write_checked(path, source):
    s=textwrap.dedent(source).lstrip(); ast.parse(s,filename=str(path))
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp"); tmp.write_text(s,encoding="utf-8",newline="\n"); os.replace(tmp,path)

def main():
    r=root()
    dep=r/"qseries_v2/oracle_adapters/independent/oad_282_gmgn_continuous_production_policy.py"
    if not dep.is_file(): raise RuntimeError("OAD-282 missing")
    mod=r/"qseries_v2/oracle_adapters/independent/oad_283_gmgn_continuous_runtime_checkpoint.py"
    test=r/"test_oad_283_gmgn_continuous_runtime_checkpoint.py"
    write_checked(mod,MODULE_SOURCE); write_checked(test,TEST_SOURCE)
    print("[PASS] OAD-282 verified")
    print("[PASS] durable restart-safe checkpoint installed")
    print("[DONE] OAD-283 INSTALLATION COMPLETE")
if __name__=="__main__": main()
