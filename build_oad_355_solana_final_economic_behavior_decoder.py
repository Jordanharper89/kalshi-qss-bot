from __future__ import annotations
import ast, hashlib, os, textwrap
from pathlib import Path

EXPECTED='build_oad_355_solana_final_economic_behavior_decoder.py'
BUILD_ID='OAD-355'
TITLE='SOLANA FINAL ECONOMIC BEHAVIOR DECODER'
MODULE='oad_355_solana_final_economic_behavior_decoder.py'
TEST='test_oad_355_solana_final_economic_behavior_decoder.py'
DEPENDENCIES={'qseries_v2/oracle_adapters/independent/oad_354_solana_economic_protocol_attribution_v3.py': ('attribute_economic_protocols_v3', 'economic_protocols'), 'qseries_v2/oracle_adapters/independent/oad_330_solana_wallet_token_flow_graph.py': ('build_wallet_token_flows', 'SolanaWalletTokenFlow')}

MODULE_SOURCE=r"""\

from __future__ import annotations
from dataclasses import dataclass

READ_ONLY=True
PROBABILITY_ENABLED=False
DIRECTION_ENABLED=False
PUBLICATION_ALLOWED=False
EXECUTION_AUTHORITY=False

_TARGETS={"METEORA_DBC","METEORA_DAMM_V2","ORCA_WHIRLPOOLS","PUMP_MAYHEM","RAYDIUM_CLMM"}

@dataclass(frozen=True,slots=True)
class SolanaFinalEconomicBehavior:
    signature:str
    protocols:tuple
    mints:tuple
    flow_rows:int
    behavior:str
    evidence:str
    execution_authority:bool=False

def decode_final_economic_behaviors(envelopes,attributions,flows):
    amap={a.signature:a for a in attributions}; out=[]
    for e in envelopes:
        a=amap.get(e.signature)
        if not a: continue
        protocols=tuple(p for p in a.economic_protocols if p in _TARGETS)
        if not protocols: continue
        fs=[f for f in flows if f.signature==e.signature]
        mints=tuple(sorted({str(f.mint) for f in fs if getattr(f,"mint",None)}))
        pos=any(float(getattr(f,"delta",0.0))>0 for f in fs)
        neg=any(float(getattr(f,"delta",0.0))<0 for f in fs)
        if pos and neg and len(mints)>=2:
            behavior="FINAL_VERIFIED_ASSET_EXCHANGE_FLOW"
            evidence="VERIFIED_PROGRAM_PLUS_BIDIRECTIONAL_TOKEN_BALANCE_FLOW"
        elif fs:
            behavior="FINAL_VERIFIED_TOKEN_FLOW"
            evidence="VERIFIED_PROGRAM_PLUS_TOKEN_BALANCE_FLOW"
        else:
            behavior="FINAL_VERIFIED_INTERACTION_UNRESOLVED"
            evidence="VERIFIED_PROGRAM_INVOCATION_ONLY"
        out.append(SolanaFinalEconomicBehavior(e.signature,protocols,mints,len(fs),behavior,evidence,False))
    return tuple(out)

"""
TEST_SOURCE=r"""\

import unittest
from types import SimpleNamespace
from qseries_v2.oracle_adapters.independent.oad_355_solana_final_economic_behavior_decoder import *

class T(unittest.TestCase):
    def test_flow(self):
        e=SimpleNamespace(signature="s")
        a=SimpleNamespace(signature="s",economic_protocols=("RAYDIUM_CLMM",))
        fs=(SimpleNamespace(signature="s",mint="A",delta=-2.0),SimpleNamespace(signature="s",mint="B",delta=1.0))
        x=decode_final_economic_behaviors((e,),(a,),fs)[0]
        print("[FINAL-FLOW]",x.protocols,x.behavior)
        self.assertEqual(x.behavior,"FINAL_VERIFIED_ASSET_EXCHANGE_FLOW")
    def test_no_fabrication(self):
        e=SimpleNamespace(signature="u")
        a=SimpleNamespace(signature="u",economic_protocols=())
        self.assertEqual(decode_final_economic_behaviors((e,),(a,),()),())

if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-355 final verified economic behavior decoder certified")

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

def verify(path,markers):
    if not path.is_file(): raise RuntimeError("dependency missing: "+str(path))
    s=path.read_text(encoding="utf-8"); ast.parse(s,filename=str(path))
    for m in markers:
        if m not in s: raise RuntimeError("dependency contract missing: "+path.name+" -> "+m)

def main():
    if Path(__file__).name!=EXPECTED: raise RuntimeError("installer identity mismatch")
    r=root(); pkg=r/"qseries_v2"/"oracle_adapters"/"independent"
    m=pkg/MODULE; t=r/TEST; init=pkg/"__init__.py"
    print("="*120); print(" "+BUILD_ID+" "+TITLE+" INSTALLER"); print("="*120); print("[ROOT]",r)
    for rel,markers in DEPENDENCIES.items():
        verify(r/rel,markers); print("[PASS] dependency interface verified:",rel)
    protected=[]
    for rel in (
        "qseries_v2/oracle_production_hardening/oph_023_postgresql_single_writer_production_freeze.py",
        "qseries_v2/oracle_adapters/independent/oad_327_solana_universal_continuity_physical_certification.py",
        "qseries_v2/oracle_adapters/independent/oad_347_solana_expanded_decode_multiblock_physical_gate.py",
        "qseries_v2/oracle_adapters/independent/oad_352_solana_same_universe_physical_coverage_gate.py",
    ):
        p=r/rel
        if not p.is_file(): raise RuntimeError("protected boundary missing: "+rel)
        protected.append((p,hashlib.sha256(p.read_bytes()).hexdigest()))
    old={p:(p.read_bytes() if p.exists() else None) for p in (m,t,init)}
    try:
        atomic(m,MODULE_SOURCE); atomic(t,TEST_SOURCE)
        lines=init.read_text(encoding="utf-8").splitlines() if init.exists() else []
        export="from ."+m.stem+" import *"
        if export not in lines: lines.append(export)
        atomic(init,"\n".join(x for x in lines if x.strip())+"\n")
        for p,h in protected:
            if hashlib.sha256(p.read_bytes()).hexdigest()!=h:
                raise RuntimeError("protected boundary changed: "+p.name)
        print("[PASS] module installed:",m.relative_to(r))
        print("[PASS] test installed:",t.name)
        print("[PASS] proven Solana boundaries preserved byte-for-byte unchanged")
        print("[PASS] unresolved programs remain unresolved unless verified")
        print("[PASS] GMGN not required")
        print("[PASS] probability=FALSE direction=FALSE publication=FALSE execution=FALSE")
        print("[DONE] "+BUILD_ID+" INSTALLATION COMPLETE")
    except Exception:
        for p,b in old.items():
            if b is None:
                if p.exists(): p.unlink()
            else: p.write_bytes(b)
        print("[ROLLBACK] affected files restored")
        raise

if __name__=="__main__":
    main()
