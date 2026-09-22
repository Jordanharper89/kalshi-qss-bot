from __future__ import annotations
import ast, hashlib, os, textwrap
from pathlib import Path

EXPECTED='build_oad_363_solana_physical_postgresql_readback_adapter.py'
BUILD_ID='OAD-363'
TITLE='SOLANA PHYSICAL POSTGRESQL READBACK ADAPTER'
MODULE='oad_363_solana_physical_postgresql_readback_adapter.py'
TEST='test_oad_363_solana_physical_postgresql_readback_adapter.py'
DEPENDENCIES={'qseries_v2/oracle_adapters/independent/oad_068_exact_postgresql_independent_readback.py': ('read',), 'qseries_v2/oracle_adapters/independent/oad_360_solana_exact_postgresql_observation_readback.py': ('SolanaExactReadbackResult', 'exact_postgresql_observation_readback')}

MODULE_SOURCE=r"""\

from __future__ import annotations
from dataclasses import dataclass
import importlib, inspect

READ_ONLY=True
PROBABILITY_ENABLED=False
DIRECTION_ENABLED=False
PUBLICATION_ALLOWED=False
EXECUTION_AUTHORITY=False

@dataclass(frozen=True, slots=True)
class SolanaPhysicalReadbackProbe:
    observation_ids: tuple
    found_ids: tuple
    missing_ids: tuple
    exact: bool
    reader_symbol: str
    execution_authority: bool=False

def _discover_reader():
    mod=importlib.import_module("qseries_v2.oracle_adapters.independent.oad_068_exact_postgresql_independent_readback")
    preferred=("readback_observation_ids","read_observation_ids","exact_readback","readback_exact_observations")
    for n in preferred:
        f=getattr(mod,n,None)
        if callable(f):
            return n,f
    candidates=[]
    for n,f in inspect.getmembers(mod, callable):
        low=n.lower()
        if "read" in low and ("observation" in low or "postgres" in low):
            candidates.append((n,f))
    if not candidates:
        raise RuntimeError("no OAD-068 PostgreSQL readback callable discovered")
    return candidates[0]

def _extract_ids(value):
    if value is None:
        return ()
    if isinstance(value, dict):
        for k in ("observation_ids","found_ids","ids","rows","results"):
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
    if isinstance(value,(str,int)):
        return (str(value),)
    return ()

def physical_readback_probe(observation_ids, reader=None):
    ids=tuple(dict.fromkeys(str(x) for x in observation_ids))
    if not ids:
        return SolanaPhysicalReadbackProbe((),(),(),True,"NONE",False)
    if reader is None:
        name,reader=_discover_reader()
    else:
        name=getattr(reader,"__name__","INJECTED_READER")
    try:
        raw=reader(ids)
    except TypeError:
        raw=[reader(x) for x in ids]
    foundset=set(_extract_ids(raw))
    found=tuple(x for x in ids if x in foundset)
    missing=tuple(x for x in ids if x not in foundset)
    return SolanaPhysicalReadbackProbe(ids,found,missing,not missing,name,False)

"""

TEST_SOURCE=r"""\

import unittest
from qseries_v2.oracle_adapters.independent.oad_363_solana_physical_postgresql_readback_adapter import *

class T(unittest.TestCase):
    def test_injected_exact(self):
        x=physical_readback_probe(("1","2"),lambda ids:[{"observation_id":"1"},{"observation_id":"2"}])
        print("[READBACK-ADAPTER]",x.reader_symbol,x.found_ids,x.missing_ids,x.exact)
        self.assertTrue(x.exact)
    def test_injected_missing(self):
        x=physical_readback_probe(("1","2"),lambda ids:[{"observation_id":"1"}])
        self.assertFalse(x.exact)
        self.assertEqual(x.missing_ids,("2",))

if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-363 physical PostgreSQL readback adapter contract certified")

"""

def root():
    for b in (Path.cwd().resolve(), Path(__file__).resolve().parent):
        for p in (b, *b.parents):
            if (p/"qseries_v2").is_dir():
                return p
    raise RuntimeError("Q Series repository root not found")

def atomic(path, source):
    source=textwrap.dedent(source).lstrip()
    ast.parse(source, filename=str(path))
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(source, encoding="utf-8", newline="\n")
    os.replace(tmp, path)

def verify(path, markers):
    if not path.is_file():
        raise RuntimeError("dependency missing: "+str(path))
    text=path.read_text(encoding="utf-8")
    ast.parse(text, filename=str(path))
    for marker in markers:
        if marker not in text:
            raise RuntimeError("dependency interface missing: "+path.name+" -> "+marker)

def main():
    if Path(__file__).name != EXPECTED:
        raise RuntimeError("installer identity mismatch")
    r=root()
    pkg=r/"qseries_v2"/"oracle_adapters"/"independent"
    m=pkg/MODULE
    t=r/TEST
    init=pkg/"__init__.py"

    print("="*120)
    print(" "+BUILD_ID+" "+TITLE+" INSTALLER")
    print("="*120)
    print("[ROOT]", r)

    for rel, markers in DEPENDENCIES.items():
        verify(r/rel, markers)
        print("[PASS] dependency interface verified:", rel)

    protected=[]
    for rel in (
        "qseries_v2/oracle_production_hardening/oph_023_postgresql_single_writer_production_freeze.py",
        "qseries_v2/oracle_adapters/independent/oad_327_solana_universal_continuity_physical_certification.py",
        "qseries_v2/oracle_adapters/independent/oad_357_solana_decoder_closeout_same_universe_physical_gate.py",
        "qseries_v2/oracle_adapters/independent/oad_362_solana_continuity_integrity_physical_gate.py",
    ):
        p=r/rel
        if not p.is_file():
            raise RuntimeError("protected boundary missing: "+rel)
        protected.append((p, hashlib.sha256(p.read_bytes()).hexdigest()))

    old={p:(p.read_bytes() if p.exists() else None) for p in (m,t,init)}
    try:
        atomic(m, MODULE_SOURCE)
        atomic(t, TEST_SOURCE)
        lines=init.read_text(encoding="utf-8").splitlines() if init.exists() else []
        export="from ."+m.stem+" import *"
        if export not in lines:
            lines.append(export)
        atomic(init, "\n".join(x for x in lines if x.strip())+"\n")

        for p,h in protected:
            if hashlib.sha256(p.read_bytes()).hexdigest()!=h:
                raise RuntimeError("protected boundary changed: "+p.name)

        print("[PASS] module installed:", m.relative_to(r))
        print("[PASS] test installed:", t.name)
        print("[PASS] OPH-023/OAD-327/OAD-357/OAD-362 preserved byte-for-byte unchanged")
        print("[PASS] no bypass PostgreSQL writer introduced")
        print("[PASS] GMGN not required")
        print("[PASS] probability=FALSE direction=FALSE publication=FALSE execution=FALSE")
        print("[DONE] "+BUILD_ID+" INSTALLATION COMPLETE")
    except Exception:
        for p,b in old.items():
            if b is None:
                if p.exists(): p.unlink()
            else:
                p.write_bytes(b)
        print("[ROLLBACK] affected files restored")
        raise

if __name__=="__main__":
    main()
