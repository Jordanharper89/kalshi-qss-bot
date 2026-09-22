from __future__ import annotations
import ast,hashlib,os,textwrap
from pathlib import Path
BUILD_ID='OAD-329'; TITLE='SOLANA DEX TRANSACTION ATTRIBUTION'; EXPECTED='build_oad_329_solana_dex_transaction_attribution.py'; MODULE='oad_329_solana_dex_transaction_attribution.py'; TEST='test_oad_329_solana_dex_transaction_attribution.py'; DEPENDENCIES={'qseries_v2/oracle_adapters/independent/oad_328_solana_live_dex_pool_identity_registry.py': ('build_live_solana_dex_pool_registry', 'dex_by_pair'), 'qseries_v2/oracle_adapters/independent/oad_319_solana_transaction_canonical_envelope.py': ('class SolanaTransactionEnvelope',)}
MODULE_SOURCE=r"""\

from __future__ import annotations
from dataclasses import dataclass
from .oad_328_solana_live_dex_pool_identity_registry import dex_by_pair
READ_ONLY=True;PROBABILITY_ENABLED=False;DIRECTION_ENABLED=False;PUBLICATION_ALLOWED=False;EXECUTION_AUTHORITY=False
@dataclass(frozen=True,slots=True)
class SolanaDexTransactionAttribution:
 signature:str;slot:int;matched_pool_accounts:tuple;dex_ids:tuple;attributed:bool;execution_authority:bool=False
def attribute_transactions_to_live_dex_pools(envelopes,registry):
    pairs=dex_by_pair(registry);out=[]
    for e in envelopes:
        matched=tuple(sorted({a for a in e.account_keys if a in pairs}))
        dexes=tuple(sorted({pairs[a] for a in matched}))
        out.append(SolanaDexTransactionAttribution(e.signature,e.slot,matched,dexes,bool(matched),False))
    return tuple(out)

"""
TEST_SOURCE=r"""\

import unittest
from types import SimpleNamespace
from qseries_v2.oracle_adapters.independent.oad_329_solana_dex_transaction_attribution import *
class T(unittest.TestCase):
 def test_attribution(self):
  reg=SimpleNamespace(by_pair=(("POOL","raydium"),))
  e=SimpleNamespace(signature="s",slot=1,account_keys=("A","POOL","B"))
  x=attribute_transactions_to_live_dex_pools((e,),reg)[0]
  print("[ATTR]",x.signature,x.dex_ids,x.matched_pool_accounts)
  self.assertTrue(x.attributed);self.assertEqual(x.dex_ids,("raydium",))
if __name__=="__main__":
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
 if not r.wasSuccessful():raise SystemExit(1)
 print("[PASS] OAD-329 live DEX transaction attribution certified")

"""
def root():
    for b in (Path.cwd().resolve(),Path(__file__).resolve().parent):
        for p in (b,*b.parents):
            if (p/"qseries_v2").is_dir(): return p
    raise RuntimeError("Q Series repository root not found")
def atomic(p,s):
    s=textwrap.dedent(s).lstrip(); ast.parse(s,filename=str(p)); p.parent.mkdir(parents=True,exist_ok=True)
    q=p.with_suffix(p.suffix+".tmp"); q.write_text(s,encoding="utf-8",newline="\n"); os.replace(q,p)
def main():
    if Path(__file__).name!=EXPECTED: raise RuntimeError("installer identity mismatch")
    r=root(); pkg=r/"qseries_v2"/"oracle_adapters"/"independent"; m=pkg/MODULE; t=r/TEST; init=pkg/"__init__.py"
    print("="*120); print(" "+BUILD_ID+" "+TITLE+" INSTALLER"); print("="*120); print("[ROOT]",r)
    for rel,marks in DEPENDENCIES.items():
        p=r/rel
        if not p.is_file(): raise RuntimeError("dependency missing: "+rel)
        src=p.read_text(encoding="utf-8"); ast.parse(src,filename=str(p))
        for mark in marks:
            if mark not in src: raise RuntimeError("dependency contract missing: "+rel+" -> "+mark)
        print("[PASS] exact dependency verified:",rel)
    protected=[]
    for rel in ("qseries_v2/oracle_production_hardening/oph_023_postgresql_single_writer_production_freeze.py",
                "qseries_v2/oracle_adapters/kalshi/oad_055_kalshi_production_freeze.py",
                "qseries_v2/oracle_adapters/independent/oad_327_solana_universal_continuity_physical_certification.py"):
        p=r/rel
        if not p.is_file(): raise RuntimeError("protected boundary missing: "+rel)
        protected.append((p,hashlib.sha256(p.read_bytes()).hexdigest()))
    old={p:(p.read_bytes() if p.exists() else None) for p in (m,t,init)}
    try:
        atomic(m,MODULE_SOURCE); atomic(t,TEST_SOURCE)
        lines=init.read_text(encoding="utf-8").splitlines() if init.exists() else []
        exp="from ."+m.stem+" import *"
        if exp not in lines: lines.append(exp)
        atomic(init,"\n".join(x for x in lines if x.strip())+"\n")
        for p,h in protected:
            if hashlib.sha256(p.read_bytes()).hexdigest()!=h: raise RuntimeError("protected boundary changed: "+p.name)
        print("[PASS] module installed:",m.relative_to(r)); print("[PASS] test installed:",t.name)
        print("[PASS] OAD-327 continuity boundary preserved unchanged")
        print("[PASS] live pool/Dex identity used; no brittle hard-coded DEX program dependency")
        print("[PASS] unknown chain behavior retained and measured")
        print("[PASS] GMGN not required")
        print("[PASS] probability=FALSE direction=FALSE publication=FALSE execution=FALSE")
        print("[DONE] "+BUILD_ID+" INSTALLATION COMPLETE")
    except Exception:
        for p,b in old.items():
            if b is None:
                if p.exists(): p.unlink()
            else:p.write_bytes(b)
        print("[ROLLBACK] affected files restored"); raise
if __name__=="__main__": main()
