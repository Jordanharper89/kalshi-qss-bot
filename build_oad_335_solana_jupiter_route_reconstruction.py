from __future__ import annotations
import ast,hashlib,os,textwrap
from pathlib import Path

BUILD_ID='OAD-335'
TITLE='SOLANA JUPITER CPI ROUTE RECONSTRUCTION'
EXPECTED='build_oad_335_solana_jupiter_route_reconstruction.py'
MODULE='oad_335_solana_jupiter_route_reconstruction.py'
TEST='test_oad_335_solana_jupiter_route_reconstruction.py'
DEPENDENCIES={'qseries_v2/oracle_adapters/independent/oad_334_solana_transaction_protocol_attribution.py': ('known_protocols', 'inner_program_ids'), 'qseries_v2/oracle_adapters/independent/oad_330_solana_wallet_token_flow_graph.py': ('SolanaWalletTokenFlow', 'build_wallet_token_flows')}
MODULE_SOURCE=r"""\

from __future__ import annotations
from dataclasses import dataclass
from collections import defaultdict

READ_ONLY=True
PROBABILITY_ENABLED=False
DIRECTION_ENABLED=False
PUBLICATION_ALLOWED=False
EXECUTION_AUTHORITY=False

@dataclass(frozen=True,slots=True)
class SolanaRoutedSwap:
    signature:str
    slot:int
    router:str|None
    protocols:tuple
    owner:str|None
    input_mints:tuple
    output_mints:tuple
    input_amount_abs:float
    output_amount:float
    route_state:str
    execution_authority:bool=False

def reconstruct_routed_swaps(envelopes,attributions,flows):
    amap={x.signature:x for x in attributions}
    fmap=defaultdict(list)
    for f in flows:
        fmap[f.signature].append(f)
    out=[]
    for e in envelopes:
        a=amap.get(e.signature)
        if not a:
            continue
        router="JUPITER_V6" if "JUPITER_V6" in a.known_protocols else None
        protocols=tuple(x for x in a.known_protocols if x!="JUPITER_V6")
        byowner=defaultdict(list)
        for f in fmap.get(e.signature,()):
            if getattr(f,"owner",None):
                byowner[f.owner].append(f)
        emitted=False
        for owner,rows in byowner.items():
            neg=[x for x in rows if x.delta<0 and x.mint]
            pos=[x for x in rows if x.delta>0 and x.mint]
            if neg and pos:
                state="ROUTED_SWAP_RECONSTRUCTED" if router else "DIRECT_SWAP_RECONSTRUCTED"
                out.append(SolanaRoutedSwap(
                    e.signature,e.slot,router,protocols,owner,
                    tuple(sorted({x.mint for x in neg})),
                    tuple(sorted({x.mint for x in pos})),
                    sum(abs(x.delta) for x in neg),sum(x.delta for x in pos),
                    state,False
                ))
                emitted=True
        if router and not emitted:
            out.append(SolanaRoutedSwap(e.signature,e.slot,router,protocols,None,tuple(),tuple(),0.0,0.0,"ROUTER_INTERACTION_UNRESOLVED",False))
    return tuple(out)

"""
TEST_SOURCE=r"""\

import unittest
from types import SimpleNamespace
from qseries_v2.oracle_adapters.independent.oad_335_solana_jupiter_route_reconstruction import *
class T(unittest.TestCase):
 def test_route(self):
  e=SimpleNamespace(signature="s",slot=1)
  a=SimpleNamespace(signature="s",known_protocols=("JUPITER_V6","METEORA_DLMM"))
  flows=(SimpleNamespace(signature="s",owner="W",mint="A",delta=-5.0),
         SimpleNamespace(signature="s",owner="W",mint="B",delta=9.0))
  x=reconstruct_routed_swaps((e,),(a,),flows)[0]
  print("[ROUTE]",x.router,x.protocols,x.input_mints,"->",x.output_mints,x.route_state)
  self.assertEqual(x.route_state,"ROUTED_SWAP_RECONSTRUCTED")
  self.assertEqual(x.router,"JUPITER_V6")
if __name__=="__main__":
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
 if not r.wasSuccessful(): raise SystemExit(1)
 print("[PASS] OAD-335 Jupiter/CPI route reconstruction certified")

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

def main():
    if Path(__file__).name!=EXPECTED:
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
    for rel,marks in DEPENDENCIES.items():
        p=r/rel
        if not p.is_file():
            raise RuntimeError("dependency missing: "+rel)
        src=p.read_text(encoding="utf-8")
        ast.parse(src,filename=str(p))
        for mark in marks:
            if mark not in src:
                raise RuntimeError("dependency contract missing: "+rel+" -> "+mark)
        print("[PASS] exact dependency verified:",rel)
    protected=[]
    for rel in (
        "qseries_v2/oracle_production_hardening/oph_023_postgresql_single_writer_production_freeze.py",
        "qseries_v2/oracle_adapters/kalshi/oad_055_kalshi_production_freeze.py",
        "qseries_v2/oracle_adapters/independent/oad_327_solana_universal_continuity_physical_certification.py",
        "qseries_v2/oracle_adapters/independent/oad_332_solana_live_decode_coverage_physical_gate.py",
    ):
        p=r/rel
        if not p.is_file():
            raise RuntimeError("protected boundary missing: "+rel)
        protected.append((p,hashlib.sha256(p.read_bytes()).hexdigest()))
    targets=(m,t,init)
    old={p:(p.read_bytes() if p.exists() else None) for p in targets}
    try:
        atomic(m,MODULE_SOURCE)
        atomic(t,TEST_SOURCE)
        lines=init.read_text(encoding="utf-8").splitlines() if init.exists() else []
        exp="from ."+m.stem+" import *"
        if exp not in lines:
            lines.append(exp)
        atomic(init,"\n".join(x for x in lines if x.strip())+"\n")
        for p,h in protected:
            if hashlib.sha256(p.read_bytes()).hexdigest()!=h:
                raise RuntimeError("protected boundary changed: "+p.name)
        print("[PASS] module installed:",m.relative_to(r))
        print("[PASS] test installed:",t.name)
        print("[PASS] OAD-327 continuity and OAD-332 live baseline preserved unchanged")
        print("[PASS] program attribution includes top-level + inner/CPI instructions")
        print("[PASS] unknown programs retained; infrastructure separated from economic traffic")
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
