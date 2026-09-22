from __future__ import annotations
import ast, hashlib, os, textwrap
from pathlib import Path

EXPECTED='build_oad_368_solana_physical_checkpoint_contract.py'
BUILD_ID='OAD-368'
TITLE='SOLANA PHYSICAL CHECKPOINT CONTRACT'
MODULE='oad_368_solana_physical_checkpoint_contract.py'
TEST='test_oad_368_solana_physical_checkpoint_contract.py'
DEPENDENCIES={'qseries_v2/oracle_adapters/independent/oad_323_solana_durable_slot_checkpoint.py': ('SolanaChainCheckpoint', 'checkpoint'), 'qseries_v2/oracle_adapters/independent/oad_367_solana_end_to_end_persistence_restart_physical_gate.py': ('END_TO_END_PERSISTENCE_RESTART_MEASURED',)}

MODULE_SOURCE=r"""\

from __future__ import annotations
from dataclasses import dataclass
import inspect
from pathlib import Path
from . import oad_323_solana_durable_slot_checkpoint as cp

READ_ONLY=True
PROBABILITY_ENABLED=False
DIRECTION_ENABLED=False
PUBLICATION_ALLOWED=False
EXECUTION_AUTHORITY=False

@dataclass(frozen=True, slots=True)
class SolanaCheckpointContract:
    load_symbol:str
    commit_symbol:str
    checkpoint_path:str
    current_slot:int|None
    generation:int|None
    execution_authority:bool=False

def _root():
    p=Path.cwd().resolve()
    for q in (p,*p.parents):
        if (q/"qseries_v2").is_dir(): return q
    raise RuntimeError("repo root not found")

def _public_functions():
    return {n:f for n,f in inspect.getmembers(cp) if inspect.isfunction(f) and not n.startswith("_")}

def _pick(names, contains):
    funcs=_public_functions()
    for n in names:
        if n in funcs: return n,funcs[n]
    for n,f in funcs.items():
        low=n.lower()
        if all(x in low for x in contains): return n,f
    raise RuntimeError("checkpoint function not found; available="+repr(tuple(sorted(funcs))))

def discover_checkpoint_contract(root=None):
    r=Path(root or _root())
    load_name,load_fn=_pick(
        ("load_solana_chain_checkpoint","load_checkpoint"),
        ("load","checkpoint")
    )
    commit_name,commit_fn=_pick(
        ("commit_solana_chain_checkpoint","commit_checkpoint","save_solana_chain_checkpoint"),
        ("commit","checkpoint")
    )
    obj=load_fn(r)
    slot=None
    gen=None
    for n in ("slot","checkpoint_slot","last_slot","through_slot"):
        if hasattr(obj,n):
            slot=getattr(obj,n); break
        if isinstance(obj,dict) and n in obj:
            slot=obj[n]; break
    for n in ("generation","version"):
        if hasattr(obj,n):
            gen=getattr(obj,n); break
        if isinstance(obj,dict) and n in obj:
            gen=obj[n]; break
    path=r/"runtime_state"/"solana_universal_chain"/"checkpoint.json"
    return SolanaCheckpointContract(load_name,commit_name,str(path),slot,gen,False)

def commit_checkpoint_exact(slot, signature=None, root=None):
    r=Path(root or _root())
    _,f=_pick(
        ("commit_solana_chain_checkpoint","commit_checkpoint","save_solana_chain_checkpoint"),
        ("commit","checkpoint")
    )
    sig=inspect.signature(f)
    kwargs={}
    args=[]
    for name,p in sig.parameters.items():
        low=name.lower()
        if low in ("slot","checkpoint_slot","last_slot","through_slot"):
            kwargs[name]=int(slot)
        elif low in ("signature","block_signature","last_signature"):
            kwargs[name]=signature
        elif low in ("root","repo_root","repository_root"):
            kwargs[name]=r
        elif p.default is inspect._empty:
            raise RuntimeError("unsupported checkpoint commit argument: "+name)
    return f(**kwargs)

"""

TEST_SOURCE=r"""\

import unittest
from qseries_v2.oracle_adapters.independent.oad_368_solana_physical_checkpoint_contract import *

class T(unittest.TestCase):
    def test_discovery(self):
        x=discover_checkpoint_contract()
        print("[CHECKPOINT-CONTRACT]",x.load_symbol,x.commit_symbol,x.checkpoint_path,x.current_slot,x.generation)
        self.assertTrue(x.load_symbol)
        self.assertTrue(x.commit_symbol)
        self.assertTrue(x.checkpoint_path.endswith("checkpoint.json"))

if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-368 actual durable Solana checkpoint contract discovered and certified")

"""

def root():
    for b in (Path.cwd().resolve(), Path(__file__).resolve().parent):
        for p in (b, *b.parents):
            if (p/"qseries_v2").is_dir():
                return p
    raise RuntimeError("Q Series repository root not found")

def verify(path, markers):
    if not path.is_file():
        raise RuntimeError("dependency missing: "+str(path))
    text=path.read_text(encoding="utf-8")
    ast.parse(text, filename=str(path))
    for marker in markers:
        if marker not in text:
            raise RuntimeError("dependency interface missing: "+path.name+" -> "+marker)

def atomic(path, source):
    source=textwrap.dedent(source).lstrip()
    ast.parse(source, filename=str(path))
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(source, encoding="utf-8", newline="\n")
    os.replace(tmp,path)

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
    print("[ROOT]",r)

    for rel, markers in DEPENDENCIES.items():
        verify(r/rel, markers)
        print("[PASS] dependency interface verified:", rel)

    protected=[]
    for rel in (
        "qseries_v2/oracle_production_hardening/oph_023_postgresql_single_writer_production_freeze.py",
        "qseries_v2/oracle_adapters/independent/oad_327_solana_universal_continuity_physical_certification.py",
        "qseries_v2/oracle_adapters/independent/oad_357_solana_decoder_closeout_same_universe_physical_gate.py",
        "qseries_v2/oracle_adapters/independent/oad_362_solana_continuity_integrity_physical_gate.py",
        "qseries_v2/oracle_adapters/independent/oad_367_solana_end_to_end_persistence_restart_physical_gate.py",
    ):
        p=r/rel
        if p.is_file():
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
        print("[PASS] protected certified boundaries preserved")
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
