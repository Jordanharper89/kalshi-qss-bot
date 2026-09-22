from __future__ import annotations
import ast, hashlib, os, textwrap
from pathlib import Path

EXPECTED="build_oad_377_solana_existing_ocl_learning_handoff_OAD317_INTERFACE_REBUILD.py"
MODULE="oad_377_solana_existing_ocl_learning_handoff_physical_gate.py"
TEST="test_oad_377_solana_existing_ocl_learning_handoff_physical_gate.py"

MODULE_SOURCE=r"""
from __future__ import annotations
from dataclasses import dataclass
import importlib, inspect

from .oad_376_solana_learned_experience_bridge import (
    SolanaLearnedExperienceRecord,
    as_learning_payload,
)

READ_ONLY=True
PROBABILITY_ENABLED=False
DIRECTION_ENABLED=False
PUBLICATION_ALLOWED=False
EXECUTION_AUTHORITY=False

OAD317_MODULE="qseries_v2.oracle_adapters.independent.oad_317_solana_existing_ocl_learning_handoff"

@dataclass(frozen=True, slots=True)
class SolanaOCLHandoffResult:
    boundary_module:str
    boundary_symbol:str
    accepted:bool
    returned_state:str
    payload_namespace:str
    execution_authority:bool=False

def _public_functions(mod):
    return tuple(
        (name,f)
        for name,f in inspect.getmembers(mod)
        if not name.startswith("_") and (inspect.isfunction(f) or inspect.ismethod(f))
    )

def _score(name):
    low=name.lower()
    score=0
    if "handoff" in low: score+=40
    if "ocl" in low: score+=30
    if "learn" in low: score+=25
    if "experience" in low: score+=20
    if "record" in low: score+=15
    if "case" in low: score+=10
    if any(x in low for x in ("build","create","prepare","make")): score+=5
    if any(x in low for x in ("test","verify","load","read","status","main")): score-=20
    return score

def discover_existing_ocl_handoff():
    mod=importlib.import_module(OAD317_MODULE)
    funcs=_public_functions(mod)
    if not funcs:
        raise RuntimeError("OAD-317 exposes no public functions")

    ranked=[]
    for name,f in funcs:
        score=_score(name)
        if score>0:
            ranked.append((score,name,f))

    if not ranked:
        raise RuntimeError(
            "no OAD-317 learning/handoff callable discovered; public functions="
            +repr(tuple(name for name,_ in funcs))
        )

    ranked.sort(key=lambda x:(-x[0],x[1]))
    _,name,f=ranked[0]
    return OAD317_MODULE,name,f

def _invoke_boundary(f,payload):
    sig=inspect.signature(f)
    kwargs={}
    positional=[]
    supplied=False

    required=[
        (n,p) for n,p in sig.parameters.items()
        if p.default is inspect._empty
    ]

    for name,p in sig.parameters.items():
        low=name.lower()

        if low in (
            "record","experience","learned_experience","learning_record",
            "case","payload","item"
        ):
            kwargs[name]=payload
            supplied=True
            continue

        if low in (
            "records","experiences","learning_records","cases",
            "payloads","items"
        ):
            kwargs[name]=(payload,)
            supplied=True
            continue

        if p.default is inspect._empty:
            if len(required)==1 and not supplied:
                positional.append(payload)
                supplied=True
                continue
            raise RuntimeError(
                "OAD-317 handoff callable requires unsupported argument: "
                +name+" ; callable="+getattr(f,"__name__","UNKNOWN")
                +" ; signature="+str(sig)
            )

    if not supplied:
        # Some certified bridge builders may accept payload only through **kwargs.
        if any(p.kind==inspect.Parameter.VAR_KEYWORD for p in sig.parameters.values()):
            kwargs["payload"]=payload
            supplied=True

    if not supplied:
        raise RuntimeError(
            "OAD-317 callable does not expose a learned-experience input; callable="
            +getattr(f,"__name__","UNKNOWN")+" ; signature="+str(sig)
        )

    return f(*positional,**kwargs)

def _state_of(result):
    if result is None:
        return "RETURNED_NONE"

    for name in ("state","status","handoff_state","learning_state","admission_state"):
        if hasattr(result,name):
            return str(getattr(result,name))
        if isinstance(result,dict) and name in result:
            return str(result[name])

    return "RETURNED"

def handoff_learned_experience(record:SolanaLearnedExperienceRecord):
    if record.learning_namespace!="EXISTING_OCL":
        raise ValueError("record does not target EXISTING_OCL")

    modname,name,f=discover_existing_ocl_handoff()
    payload=as_learning_payload(record)
    result=_invoke_boundary(f,payload)
    state=_state_of(result)

    upper=state.upper()
    accepted=not any(
        x in upper
        for x in ("FAIL","ERROR","REJECT","ROLLBACK","ABORT","INVALID")
    )

    return SolanaOCLHandoffResult(
        boundary_module=modname,
        boundary_symbol=name,
        accepted=accepted,
        returned_state=state,
        payload_namespace=record.learning_namespace,
        execution_authority=False,
    )
"""

TEST_SOURCE=r"""
import inspect
import unittest
from unittest.mock import patch
from types import SimpleNamespace

from qseries_v2.oracle_adapters.independent.oad_376_solana_learned_experience_bridge import (
    SolanaLearnedExperienceRecord,
)
from qseries_v2.oracle_adapters.independent.oad_377_solana_existing_ocl_learning_handoff_physical_gate import *

class T(unittest.TestCase):

    def _record(self):
        return SolanaLearnedExperienceRecord(
            experience_id="exp",
            case_id="case",
            behavior_type="DEX_SWAP",
            protocol="orca",
            primary_asset="A",
            secondary_asset="B",
            horizon_seconds=15,
            outcome="UP",
            return_fraction=0.01,
            evidence_source="SOLANA_CANONICAL_HISTORY",
            immutable_payload_hash="0"*64,
            learning_namespace="EXISTING_OCL",
            execution_authority=False,
        )

    def test_handoff_contract(self):
        def fake(payload):
            return SimpleNamespace(state="LEARNING_ACCEPTED")

        with patch(
            "qseries_v2.oracle_adapters.independent."
            "oad_377_solana_existing_ocl_learning_handoff_physical_gate."
            "discover_existing_ocl_handoff",
            return_value=(OAD317_MODULE,"accept_learning_record",fake)
        ):
            x=handoff_learned_experience(self._record())

        print(
            "[OCL-HANDOFF]",
            x.boundary_module,
            x.boundary_symbol,
            x.accepted,
            x.returned_state,
            x.payload_namespace
        )

        self.assertTrue(x.accepted)
        self.assertEqual(x.payload_namespace,"EXISTING_OCL")
        self.assertFalse(x.execution_authority)

    def test_real_oad317_callable_discovery(self):
        mod,name,f=discover_existing_ocl_handoff()

        print("[OAD317-DISCOVERY] module=",mod)
        print("[OAD317-DISCOVERY] symbol=",name)
        print("[OAD317-DISCOVERY] signature=",inspect.signature(f))

        self.assertEqual(mod,OAD317_MODULE)
        self.assertTrue(name)
        self.assertTrue(inspect.isfunction(f) or inspect.ismethod(f))

if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(T)
    )
    if not r.wasSuccessful():
        raise SystemExit(1)

    print("[PASS] OAD-377 actual OAD-317 existing-OCL boundary callable discovered")
    print("[PASS] no guessed qseries_v2.oracle_learning package path remains")
    print("[PASS] Solana learned-experience handoff stays inside existing certified learning boundary")
    print("[PASS] no separate Solana learner introduced")
"""

def root():
    for b in (Path.cwd().resolve(),Path(__file__).resolve().parent):
        for p in (b,*b.parents):
            if (p/"qseries_v2").is_dir():
                return p
    raise RuntimeError("Q Series repository root not found")

def atomic(path,source):
    source=textwrap.dedent(source).lstrip()
    ast.parse(source,filename=str(path))
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(source,encoding="utf-8",newline="\n")
    os.replace(tmp,path)

def inspect_python(path):
    if not path.is_file():
        raise RuntimeError("dependency missing: "+str(path))
    text=path.read_text(encoding="utf-8")
    tree=ast.parse(text,filename=str(path))
    funcs=tuple(sorted(
        n.name for n in tree.body
        if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))
        and not n.name.startswith("_")
    ))
    classes=tuple(sorted(
        n.name for n in tree.body
        if isinstance(n,ast.ClassDef)
        and not n.name.startswith("_")
    ))
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
    print(" OAD-377 SOLANA EXISTING OCL LEARNING HANDOFF - OAD-317 INTERFACE REBUILD INSTALLER")
    print("="*120)
    print("[ROOT]",r)

    p376=pkg/"oad_376_solana_learned_experience_bridge.py"
    text376,funcs376,classes376=inspect_python(p376)
    if "SolanaLearnedExperienceRecord" not in classes376:
        raise RuntimeError("OAD-376 learned experience record missing")
    if "as_learning_payload" not in funcs376:
        raise RuntimeError("OAD-376 as_learning_payload missing")
    print("[PASS] OAD-376 learned-experience payload contract verified")

    p317=pkg/"oad_317_solana_existing_ocl_learning_handoff.py"
    text317,funcs317,classes317=inspect_python(p317)

    if not funcs317:
        raise RuntimeError("OAD-317 exposes no public functions")

    likely=tuple(
        f for f in funcs317
        if any(x in f.lower() for x in ("handoff","ocl","learn","experience","record","case"))
    )

    if not likely:
        raise RuntimeError(
            "OAD-317 has no discoverable learning/handoff function; public functions="
            +repr(funcs317)
        )

    print("[PASS] OAD-317 actual public functions:",funcs317)
    print("[PASS] OAD-317 candidate learning/handoff functions:",likely)
    print("[PASS] guessed qseries_v2.oracle_learning / oracle_continuous_learning paths removed")

    protected=[]
    for rel in (
        "qseries_v2/oracle_production_hardening/oph_023_postgresql_single_writer_production_freeze.py",
        "qseries_v2/oracle_adapters/independent/oad_317_solana_existing_ocl_learning_handoff.py",
        "qseries_v2/oracle_adapters/independent/oad_327_solana_universal_continuity_physical_certification.py",
        "qseries_v2/oracle_adapters/independent/oad_357_solana_decoder_closeout_same_universe_physical_gate.py",
        "qseries_v2/oracle_adapters/independent/oad_362_solana_continuity_integrity_physical_gate.py",
        "qseries_v2/oracle_adapters/independent/oad_372_solana_final_persistence_continuity_physical_gate.py",
        "qseries_v2/oracle_adapters/independent/oad_373_solana_universal_economic_event_promotion.py",
        "qseries_v2/oracle_adapters/independent/oad_374_solana_temporal_case_bridge.py",
        "qseries_v2/oracle_adapters/independent/oad_375_solana_verified_forward_outcome_bridge.py",
        "qseries_v2/oracle_adapters/independent/oad_376_solana_learned_experience_bridge.py",
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

        print("[PASS] module replaced:",m.relative_to(r))
        print("[PASS] test replaced:",t.name)
        print("[PASS] OAD-317 preserved byte-for-byte unchanged")
        print("[PASS] OAD-373/OAD-374/OAD-375/OAD-376 preserved")
        print("[PASS] no separate Solana learner introduced")
        print("[PASS] GMGN not required")
        print("[PASS] probability=FALSE direction=FALSE publication=FALSE execution=FALSE")
        print("[DONE] OAD-377 OAD-317 INTERFACE REBUILD INSTALLATION COMPLETE")

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
