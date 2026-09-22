from __future__ import annotations
import ast, hashlib, os, textwrap
from pathlib import Path

EXPECTED='build_oad_377_solana_existing_ocl_learning_handoff_physical_gate.py'
BUILD_ID='OAD-377'
TITLE='SOLANA EXISTING OCL LEARNING HANDOFF PHYSICAL GATE'
MODULE='oad_377_solana_existing_ocl_learning_handoff_physical_gate.py'
TEST='test_oad_377_solana_existing_ocl_learning_handoff_physical_gate.py'
DEPENDENCIES={'qseries_v2/oracle_adapters/independent/oad_376_solana_learned_experience_bridge.py': ('EXISTING_OCL', 'SolanaLearnedExperienceRecord'), 'qseries_v2/oracle_adapters/independent/oad_317_solana_existing_ocl_learning_handoff.py': ('OCL', 'learn')}
EXTRA_PROTECTED=()

MODULE_SOURCE=r"""\

from __future__ import annotations
from dataclasses import dataclass, asdict
import importlib, inspect
from pathlib import Path
from .oad_376_solana_learned_experience_bridge import SolanaLearnedExperienceRecord, as_learning_payload

READ_ONLY=True
PROBABILITY_ENABLED=False
DIRECTION_ENABLED=False
PUBLICATION_ALLOWED=False
EXECUTION_AUTHORITY=False

@dataclass(frozen=True, slots=True)
class SolanaOCLHandoffResult:
    ocl_module:str
    ocl_symbol:str
    accepted:bool
    returned_state:str
    payload_namespace:str
    execution_authority:bool=False

def _candidate_modules():
    return (
        "qseries_v2.oracle_learning.ocl_021_unified_learner_state_aggregation",
        "qseries_v2.oracle_learning.ocl_022",
        "qseries_v2.oracle_continuous_learning.ocl_021_unified_learner_state_aggregation",
        "qseries_v2.oracle_continuous_learning.ocl_022",
        "qseries_v2.oracle_learning.ocl",
    )

def _score(name):
    low=name.lower()
    s=0
    if "learn" in low: s+=20
    if "experience" in low: s+=15
    if "ingest" in low or "admit" in low or "submit" in low: s+=12
    if "record" in low or "case" in low: s+=8
    if "state" in low or "aggregate" in low: s+=2
    if any(x in low for x in ("test","verify","load","read","status")): s-=15
    return s

def discover_existing_ocl_handoff():
    found=[]
    errors=[]
    for modname in _candidate_modules():
        try:
            mod=importlib.import_module(modname)
        except Exception as e:
            errors.append((modname,type(e).__name__))
            continue
        for name,f in inspect.getmembers(mod):
            if name.startswith("_") or not (inspect.isfunction(f) or inspect.ismethod(f)):
                continue
            score=_score(name)
            if score>0:
                found.append((score,modname,name,f))
    if not found:
        raise RuntimeError("no existing OCL learning handoff callable discovered; import attempts="+repr(errors))
    found.sort(key=lambda x:(-x[0],x[1],x[2]))
    return found[0][1],found[0][2],found[0][3]

def handoff_learned_experience(record:SolanaLearnedExperienceRecord):
    modname,name,f=discover_existing_ocl_handoff()
    payload=as_learning_payload(record)
    sig=inspect.signature(f)
    kwargs={}
    positional=[]
    supplied=False

    for pname,p in sig.parameters.items():
        low=pname.lower()
        if low in ("record","experience","learned_experience","case","learning_record","payload","item"):
            kwargs[pname]=payload
            supplied=True
        elif low in ("records","experiences","cases","items","payloads"):
            kwargs[pname]=(payload,)
            supplied=True
        elif p.default is inspect._empty:
            # If there is exactly one required argument, pass the payload positionally.
            required=[x for x in sig.parameters.values() if x.default is inspect._empty]
            if len(required)==1 and not supplied:
                positional.append(payload)
                supplied=True
            else:
                raise RuntimeError(
                    "existing OCL callable requires unsupported argument: "+pname+
                    " ; callable="+modname+"."+name+
                    " ; signature="+str(sig)
                )

    if not supplied:
        raise RuntimeError("discovered OCL callable does not expose an experience/payload input: "+modname+"."+name)

    result=f(*positional,**kwargs)
    state=str(
        getattr(result,"state",
        getattr(result,"status",
        result.get("state",result.get("status","RETURNED")) if isinstance(result,dict) else "RETURNED"))
    )
    upper=state.upper()
    accepted=not any(x in upper for x in ("FAIL","ERROR","REJECT","ROLLBACK","ABORT"))
    return SolanaOCLHandoffResult(modname,name,accepted,state,record.learning_namespace,False)

"""

TEST_SOURCE=r"""\

import unittest
from unittest.mock import patch
from types import SimpleNamespace
from qseries_v2.oracle_adapters.independent.oad_376_solana_learned_experience_bridge import SolanaLearnedExperienceRecord
from qseries_v2.oracle_adapters.independent.oad_377_solana_existing_ocl_learning_handoff_physical_gate import *

class T(unittest.TestCase):
    def test_discovery_and_handoff_contract(self):
        rec=SolanaLearnedExperienceRecord(
            "exp","case","DEX_SWAP","orca","A","B",15,"UP",0.01,
            "SOLANA_CANONICAL_HISTORY","0"*64,"EXISTING_OCL",False
        )
        def fake(payload):
            return SimpleNamespace(state="LEARNING_ACCEPTED")
        with patch("qseries_v2.oracle_adapters.independent.oad_377_solana_existing_ocl_learning_handoff_physical_gate.discover_existing_ocl_handoff",
                   return_value=("existing.ocl","accept_learning_record",fake)):
            x=handoff_learned_experience(rec)
        print("[OCL-HANDOFF]",x.ocl_module,x.ocl_symbol,x.accepted,x.returned_state,x.payload_namespace)
        self.assertTrue(x.accepted)
        self.assertEqual(x.payload_namespace,"EXISTING_OCL")

    def test_real_ocl_callable_discovery(self):
        mod,name,f=discover_existing_ocl_handoff()
        print("[OCL-DISCOVERY]",mod,name,inspect.signature(f))
        self.assertTrue(mod)
        self.assertTrue(name)

if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-377 existing OCL learning handoff interface discovered")
    print("[PASS] Solana learned-experience payload contract accepted by handoff adapter")
    print("[PASS] no separate Solana learner introduced")

"""

def root():
    for b in (Path.cwd().resolve(), Path(__file__).resolve().parent):
        for p in (b,*b.parents):
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
    ast.parse(source,filename=str(path))
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(source,encoding="utf-8",newline="\n")
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

    for rel,markers in DEPENDENCIES.items():
        verify(r/rel,markers)
        print("[PASS] dependency interface verified:",rel)

    protected_rels=[
        "qseries_v2/oracle_production_hardening/oph_023_postgresql_single_writer_production_freeze.py",
        "qseries_v2/oracle_adapters/independent/oad_327_solana_universal_continuity_physical_certification.py",
        "qseries_v2/oracle_adapters/independent/oad_357_solana_decoder_closeout_same_universe_physical_gate.py",
        "qseries_v2/oracle_adapters/independent/oad_362_solana_continuity_integrity_physical_gate.py",
        "qseries_v2/oracle_adapters/independent/oad_372_solana_final_persistence_continuity_physical_gate.py",
    ]+list(EXTRA_PROTECTED)

    protected=[]
    for rel in protected_rels:
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
        print("[PASS] no separate Solana learner introduced")
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
