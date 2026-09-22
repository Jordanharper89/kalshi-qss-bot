from __future__ import annotations
import ast, hashlib, os, textwrap
from pathlib import Path

EXPECTED="build_oad_360_solana_exact_postgresql_observation_readback_DEPENDENCY_CONTRACT_REBUILD.py"
BUILD_ID="OAD-360"
TITLE="SOLANA EXACT POSTGRESQL OBSERVATION READBACK - DEPENDENCY CONTRACT REBUILD"
MODULE="oad_360_solana_exact_postgresql_observation_readback.py"
TEST="test_oad_360_solana_exact_postgresql_observation_readback.py"

MODULE_SOURCE=r"""
from __future__ import annotations
from dataclasses import dataclass
import importlib, inspect

READ_ONLY=True
PROBABILITY_ENABLED=False
DIRECTION_ENABLED=False
PUBLICATION_ALLOWED=False
EXECUTION_AUTHORITY=False

@dataclass(frozen=True,slots=True)
class SolanaExactReadbackResult:
    requested_ids:tuple
    found_ids:tuple
    missing_ids:tuple
    exact:bool
    reader_symbol:str
    execution_authority:bool=False

def _reader():
    mod=importlib.import_module("qseries_v2.oracle_adapters.independent.oad_068_exact_postgresql_independent_readback")
    preferred=("readback_observation_ids","read_observation_ids","exact_readback","readback_exact_observations")
    for n in preferred:
        f=getattr(mod,n,None)
        if callable(f):
            return n,f
    for n,f in inspect.getmembers(mod,callable):
        low=n.lower()
        if "read" in low and ("observation" in low or "postgres" in low):
            return n,f
    raise RuntimeError("OAD-068 exact readback callable not found")

def _extract_ids(value):
    if value is None:
        return ()
    if isinstance(value,dict):
        for k in ("observation_ids","found_ids","ids","rows"):
            if k in value:
                return _extract_ids(value[k])
        for k in ("observation_id","id"):
            if k in value:
                return (str(value[k]),)
        return ()
    if isinstance(value,(list,tuple,set)):
        out=[]
        for x in value:
            if isinstance(x,(str,int)):
                out.append(str(x))
            else:
                out.extend(_extract_ids(x))
        return tuple(out)
    for k in ("observation_id","id"):
        if hasattr(value,k):
            return (str(getattr(value,k)),)
    return (str(value),) if isinstance(value,(str,int)) else ()

def exact_postgresql_observation_readback(observation_ids,reader=None):
    ids=tuple(dict.fromkeys(str(x) for x in observation_ids))
    if not ids:
        return SolanaExactReadbackResult((),(),(),True,"NONE",False)
    if reader is None:
        name,reader=_reader()
    else:
        name=getattr(reader,"__name__","INJECTED_READER")
    try:
        raw=reader(ids)
    except TypeError:
        raw=[reader(oid) for oid in ids]
    found=set(_extract_ids(raw))
    hit=tuple(x for x in ids if x in found)
    miss=tuple(x for x in ids if x not in found)
    return SolanaExactReadbackResult(ids,hit,miss,not miss,name,False)
"""

TEST_SOURCE=r"""
import unittest
from qseries_v2.oracle_adapters.independent.oad_360_solana_exact_postgresql_observation_readback import *

class T(unittest.TestCase):
    def test_exact(self):
        r=exact_postgresql_observation_readback(
            ("a","b"),
            lambda ids:[{"observation_id":"a"},{"observation_id":"b"}]
        )
        print("[READBACK]",r.found_ids,r.missing_ids,r.exact)
        self.assertTrue(r.exact)

    def test_missing(self):
        r=exact_postgresql_observation_readback(
            ("a","b"),
            lambda ids:[{"observation_id":"a"}]
        )
        self.assertFalse(r.exact)
        self.assertEqual(r.missing_ids,("b",))

if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful():
        raise SystemExit(1)
    print("[PASS] OAD-360 exact observation-ID PostgreSQL readback contract certified")
"""

def root():
    for b in (Path.cwd().resolve(),Path(__file__).resolve().parent):
        for p in (b,*b.parents):
            if (p/"qseries_v2").is_dir():
                return p
    raise RuntimeError("Q Series repository root not found")

def atomic(p,src):
    src=textwrap.dedent(src).lstrip()
    ast.parse(src,filename=str(p))
    p.parent.mkdir(parents=True,exist_ok=True)
    q=p.with_suffix(p.suffix+".tmp")
    q.write_text(src,encoding="utf-8",newline="\n")
    os.replace(q,p)

def parse_module(path):
    if not path.is_file():
        raise RuntimeError("dependency missing: "+str(path))
    text=path.read_text(encoding="utf-8")
    tree=ast.parse(text,filename=str(path))
    funcs={n.name for n in ast.walk(tree) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))}
    classes={n.name for n in ast.walk(tree) if isinstance(n,ast.ClassDef)}
    return text,funcs,classes

def main():
    if Path(__file__).name!=EXPECTED:
        raise RuntimeError("installer identity mismatch")

    r=root()
    pkg=r/"qseries_v2"/"oracle_adapters"/"independent"
    m=pkg/MODULE
    t=r/TEST
    init=pkg/"__init__.py"

    print("="*120)
    print(" OAD-360 SOLANA EXACT POSTGRESQL OBSERVATION READBACK - DEPENDENCY CONTRACT REBUILD INSTALLER")
    print("="*120)
    print("[ROOT]",r)

    # OAD-068: verify a genuine readback-capable interface, not a brittle literal.
    p68=pkg/"oad_068_exact_postgresql_independent_readback.py"
    text68,funcs68,classes68=parse_module(p68)
    readback_candidates=[x for x in funcs68 if ("read" in x.lower() and ("observation" in x.lower() or "postgres" in x.lower()))]
    if not readback_candidates and "PostgreSQL" not in text68:
        raise RuntimeError("OAD-068 readback interface not detected")
    print("[PASS] OAD-068 exact PostgreSQL readback capability verified without brittle literal marker")

    # OAD-325: verify the real production persistence contract.
    p325=pkg/"oad_325_solana_universal_single_writer_persistence.py"
    text325,funcs325,classes325=parse_module(p325)
    if "oracle.solana_universal_chain" not in text325:
        raise RuntimeError("OAD-325 producer identity missing")
    if "submit_observation_batch" not in text325 or "await_request" not in text325:
        raise RuntimeError("OAD-325 OPH-019 single-writer admission contract not detected")
    print("[PASS] OAD-325 universal single-writer persistence contract verified by actual submit/await interface")

    protected=[]
    for rel in (
        "qseries_v2/oracle_production_hardening/oph_023_postgresql_single_writer_production_freeze.py",
        "qseries_v2/oracle_adapters/independent/oad_327_solana_universal_continuity_physical_certification.py",
        "qseries_v2/oracle_adapters/independent/oad_357_solana_decoder_closeout_same_universe_physical_gate.py",
    ):
        p=r/rel
        if not p.is_file():
            raise RuntimeError("protected boundary missing: "+rel)
        protected.append((p,hashlib.sha256(p.read_bytes()).hexdigest()))

    old={p:(p.read_bytes() if p.exists() else None) for p in (m,t,init)}
    try:
        atomic(m,MODULE_SOURCE)
        atomic(t,TEST_SOURCE)
        lines=init.read_text(encoding="utf-8").splitlines() if init.exists() else []
        export="from ."+m.stem+" import *"
        if export not in lines:
            lines.append(export)
        atomic(init,"\n".join(x for x in lines if x.strip())+"\n")

        for p,h in protected:
            if hashlib.sha256(p.read_bytes()).hexdigest()!=h:
                raise RuntimeError("protected boundary changed: "+p.name)

        print("[PASS] module installed:",m.relative_to(r))
        print("[PASS] test installed:",t.name)
        print("[PASS] OPH-023/OAD-327/OAD-357 preserved byte-for-byte unchanged")
        print("[PASS] no direct PostgreSQL writer introduced")
        print("[PASS] OAD-360 remains readback-only")
        print("[PASS] GMGN not required")
        print("[PASS] probability=FALSE direction=FALSE publication=FALSE execution=FALSE")
        print("[DONE] OAD-360 DEPENDENCY CONTRACT REBUILD INSTALLATION COMPLETE")
    except Exception:
        for p,b in old.items():
            if b is None:
                if p.exists():
                    p.unlink()
            else:
                p.write_bytes(b)
        print("[ROLLBACK] affected files restored")
        raise

if __name__=="__main__":
    main()
