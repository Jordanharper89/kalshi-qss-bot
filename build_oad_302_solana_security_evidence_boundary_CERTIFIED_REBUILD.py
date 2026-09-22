from __future__ import annotations
import ast,hashlib,os,textwrap
from pathlib import Path
BUILD_ID='OAD-302'
TITLE='SOLANA SECURITY EVIDENCE BOUNDARY'
EXPECTED='build_oad_302_solana_security_evidence_boundary_CERTIFIED_REBUILD.py'
MODULE='oad_302_solana_security_evidence_boundary.py'
TEST='test_oad_302_solana_security_evidence_boundary.py'
DEPENDENCIES=[('qseries_v2/oracle_adapters/independent/oad_288_gmgn_clean_acquisition_boundary.py', ('def acquire_gmgn_token', 'class GMGNAcquisition')), ('qseries_v2/oracle_adapters/independent/oad_292_solana_bounded_multisource_token_universe.py', ('def discover_bounded_multisource_solana_universe',))]
MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass\nfrom .oad_288_gmgn_clean_acquisition_boundary import acquire_gmgn_token\nfrom .oad_292_solana_bounded_multisource_token_universe import discover_bounded_multisource_solana_universe\nREAD_ONLY=True; PROBABILITY_ENABLED=False; DIRECTION_ENABLED=False; PUBLICATION_ALLOWED=False; EXECUTION_AUTHORITY=False\n@dataclass(frozen=True,slots=True)\nclass SolanaSecurityEvidence:\n    token_address:str; gmgn_security:dict; provider_claim_only:bool=True; execution_authority:bool=False\ndef acquire_solana_security_evidence(token_address,timeout_seconds=30.0):\n    token=str(token_address).strip()\n    if not token: raise ValueError("token_address required")\n    x=acquire_gmgn_token(token,timeout_seconds)\n    sec=(x.payload or {}).get("security")\n    if not isinstance(sec,dict): raise RuntimeError("GMGN security section missing or non-object")\n    return SolanaSecurityEvidence(token,sec,True,False)\ndef acquire_current_solana_security_evidence(timeout_seconds=30.0):\n    u=discover_bounded_multisource_solana_universe(timeout_seconds); errors=[]\n    for c in u.candidates:\n        try: return acquire_solana_security_evidence(c.token_address,timeout_seconds)\n        except Exception as e: errors.append(c.token_address+":"+type(e).__name__+":"+str(e)[:100])\n    raise RuntimeError("no bounded Solana token completed GMGN security acquisition: "+" | ".join(errors[:5]))\n'
TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_adapters.independent.oad_302_solana_security_evidence_boundary import *\nclass T(unittest.TestCase):\n    def test_physical(self):\n        x=acquire_current_solana_security_evidence()\n        print("[PHYSICAL] token=",x.token_address); print("[PHYSICAL] security_fields=",len(x.gmgn_security))\n        self.assertTrue(x.token_address); self.assertIsInstance(x.gmgn_security,dict)\n        self.assertTrue(x.provider_claim_only); self.assertFalse(x.execution_authority)\nif __name__=="__main__":\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] OAD-302 GMGN Solana security evidence physically certified as provider claim")\n'
def root():
    for b in (Path.cwd().resolve(),Path(__file__).resolve().parent):
        for p in (b,*b.parents):
            if (p/"qseries_v2").is_dir(): return p
    raise RuntimeError("Q Series repository root not found")
def checked_write(p,s):
    s=textwrap.dedent(s).lstrip(); ast.parse(s,filename=str(p))
    p.parent.mkdir(parents=True,exist_ok=True); q=p.with_suffix(p.suffix+".tmp")
    q.write_text(s,encoding="utf-8",newline="\n"); os.replace(q,p)
def main():
    if Path(__file__).name!=EXPECTED: raise RuntimeError("installer filename identity mismatch")
    r=root(); pkg=r/"qseries_v2"/"oracle_adapters"/"independent"; m=pkg/MODULE; t=r/TEST; init=pkg/"__init__.py"
    print("="*120); print(" "+BUILD_ID+" "+TITLE+" — CERTIFIED REBUILD INSTALLER"); print("="*120); print("[ROOT]",r)
    for rel,marks in DEPENDENCIES:
        p=r/rel
        if not p.is_file(): raise RuntimeError("dependency missing: "+rel)
        s=p.read_text(encoding="utf-8"); ast.parse(s,filename=str(p))
        for mark in marks:
            if mark not in s: raise RuntimeError("exact dependency marker missing: "+rel+" -> "+mark)
        print("[PASS] exact dependency verified:",rel)
    protected=[]
    for rel in ("qseries_v2/oracle_production_hardening/oph_023_postgresql_single_writer_production_freeze.py","qseries_v2/oracle_adapters/kalshi/oad_055_kalshi_production_freeze.py"):
        p=r/rel
        if not p.is_file(): raise RuntimeError("frozen boundary missing: "+rel)
        protected.append((p,hashlib.sha256(p.read_bytes()).hexdigest()))
    old={p:(p.read_bytes() if p.exists() else None) for p in (m,t,init)}
    try:
        checked_write(m,MODULE_SOURCE); checked_write(t,TEST_SOURCE)
        lines=init.read_text(encoding="utf-8").splitlines() if init.exists() else []
        exp="from ."+m.stem+" import *"
        if exp not in lines: lines.append(exp)
        checked_write(init,"\n".join(x for x in lines if x.strip())+"\n")
        for p,h in protected:
            if hashlib.sha256(p.read_bytes()).hexdigest()!=h: raise RuntimeError("frozen boundary changed: "+p.name)
        print("[PASS] module installed:",m.relative_to(r)); print("[PASS] test installed:",t.name)
        print("[PASS] frozen OPH-023/Kalshi OAD-055 unchanged")
        print("[PASS] probability=FALSE direction=FALSE publication=FALSE execution=FALSE")
        print("[DONE] "+BUILD_ID+" CERTIFIED REBUILD INSTALLATION COMPLETE")
    except Exception:
        for p,b in old.items():
            if b is None:
                if p.exists(): p.unlink()
            else: p.write_bytes(b)
        print("[ROLLBACK] affected files restored"); raise
if __name__=="__main__": main()
