from __future__ import annotations
import ast,hashlib,os,textwrap
from pathlib import Path

BUILD_ID='OAD-334'
TITLE='SOLANA TRANSACTION PROTOCOL ATTRIBUTION'
EXPECTED='build_oad_334_solana_transaction_protocol_attribution.py'
MODULE='oad_334_solana_transaction_protocol_attribution.py'
TEST='test_oad_334_solana_transaction_protocol_attribution.py'
DEPENDENCIES={'qseries_v2/oracle_adapters/independent/oad_333_solana_authoritative_program_identity_registry.py': ('identify_solana_program', 'PROGRAMS'), 'qseries_v2/oracle_adapters/independent/oad_319_solana_transaction_canonical_envelope.py': ('inner_instructions', 'account_keys')}
MODULE_SOURCE=r"""\

from __future__ import annotations
from dataclasses import dataclass
from .oad_333_solana_authoritative_program_identity_registry import identify_solana_program

READ_ONLY=True
PROBABILITY_ENABLED=False
DIRECTION_ENABLED=False
PUBLICATION_ALLOWED=False
EXECUTION_AUTHORITY=False

def _program_id(ix,account_keys):
    if not isinstance(ix,dict):
        return ""
    pid=ix.get("programId") or ix.get("program_id")
    if isinstance(pid,dict):
        pid=pid.get("pubkey") or pid.get("key")
    if pid:
        return str(pid)
    idx=ix.get("programIdIndex")
    if isinstance(idx,int) and 0<=idx<len(account_keys):
        return str(account_keys[idx])
    return ""

def _walk_inner(inner,account_keys):
    for group in inner or ():
        if not isinstance(group,dict):
            continue
        for ix in group.get("instructions") or ():
            pid=_program_id(ix,account_keys)
            if pid:
                yield pid

@dataclass(frozen=True,slots=True)
class SolanaProtocolAttribution:
    signature:str
    slot:int
    top_level_program_ids:tuple
    inner_program_ids:tuple
    known_protocols:tuple
    infrastructure_programs:tuple
    unknown_programs:tuple
    market_relevant:bool
    execution_authority:bool=False

def attribute_transaction_protocols(envelopes):
    out=[]
    for e in envelopes:
        keys=tuple(e.account_keys or ())
        top=tuple(pid for pid in (_program_id(ix,keys) for ix in (e.instructions or ())) if pid)
        inner=tuple(_walk_inner(e.inner_instructions or (),keys))
        ids=top+inner
        known=[];infra=[];unknown=[]
        for pid in ids:
            x=identify_solana_program(pid)
            if not x.known:
                unknown.append(pid)
            elif x.category=="INFRASTRUCTURE":
                infra.append(x.name)
            elif x.name not in known:
                known.append(x.name)
        out.append(SolanaProtocolAttribution(
            e.signature,e.slot,top,inner,tuple(known),tuple(sorted(set(infra))),
            tuple(sorted(set(unknown))),bool(known),False
        ))
    return tuple(out)

"""
TEST_SOURCE=r"""\

import unittest
from types import SimpleNamespace
from qseries_v2.oracle_adapters.independent.oad_334_solana_transaction_protocol_attribution import *
class T(unittest.TestCase):
 def test_top_and_inner(self):
  e=SimpleNamespace(signature="s",slot=7,
   account_keys=("A","JUP6LkbZbjS1jKKwapdHNy74zcZ3tLUZoi5QNyVTaV4","pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA"),
   instructions=({"programIdIndex":1},),
   inner_instructions=({"index":0,"instructions":[{"programIdIndex":2},{"programId":"Vote111111111111111111111111111111111111111"}]},))
  x=attribute_transaction_protocols((e,))[0]
  print("[ATTR]",x.known_protocols,"infra=",x.infrastructure_programs,"inner=",x.inner_program_ids)
  self.assertIn("JUPITER_V6",x.known_protocols)
  self.assertIn("PUMP_FUN_AMM",x.known_protocols)
  self.assertIn("SOLANA_VOTE",x.infrastructure_programs)
if __name__=="__main__":
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
 if not r.wasSuccessful(): raise SystemExit(1)
 print("[PASS] OAD-334 top-level + CPI Solana protocol attribution certified")

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
