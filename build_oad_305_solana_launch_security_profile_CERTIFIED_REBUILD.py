from __future__ import annotations
import ast,hashlib,os,textwrap
from pathlib import Path
BUILD_ID='OAD-305'
TITLE='SOLANA LAUNCH / SECURITY PROFILE'
EXPECTED='build_oad_305_solana_launch_security_profile_CERTIFIED_REBUILD.py'
MODULE='oad_305_solana_launch_security_profile.py'
TEST='test_oad_305_solana_launch_security_profile.py'
DEPENDENCIES=[('qseries_v2/oracle_adapters/independent/oad_303_solana_mint_authority_supply_evidence.py', ('def acquire_current_mint_authority_supply_evidence',)), ('qseries_v2/oracle_adapters/independent/oad_304_solana_creator_deployer_claim_intelligence.py', ('def _extract', 'class CreatorDeployerClaim'))]
MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass\nfrom .oad_303_solana_mint_authority_supply_evidence import acquire_current_mint_authority_supply_evidence\nfrom .oad_304_solana_creator_deployer_claim_intelligence import _extract\nREAD_ONLY=True; PROBABILITY_ENABLED=False; DIRECTION_ENABLED=False; PUBLICATION_ALLOWED=False; EXECUTION_AUTHORITY=False\n@dataclass(frozen=True,slots=True)\nclass SolanaLaunchSecurityProfile:\n    token_address:str; chain_mint_payload:dict; gmgn_security:dict; creator_deployer_claims:tuple; evidence_state:str; execution_authority:bool=False\ndef build_current_solana_launch_security_profile(timeout_seconds=30.0):\n    x=acquire_current_mint_authority_supply_evidence(timeout_seconds)\n    claims=tuple(_extract(x.token_address,x.gmgn_security))\n    return SolanaLaunchSecurityProfile(x.token_address,dict(x.chain_observation.payload),dict(x.gmgn_security),claims,"INDEPENDENT_CHAIN_AND_PROVIDER_EVIDENCE_UNBLENDED",False)\n'
TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_adapters.independent.oad_305_solana_launch_security_profile import *\nclass T(unittest.TestCase):\n    def test_physical(self):\n        x=build_current_solana_launch_security_profile()\n        print("[PHYSICAL] token=",x.token_address); print("[PHYSICAL] evidence_state=",x.evidence_state); print("[PHYSICAL] creator_claims=",len(x.creator_deployer_claims))\n        self.assertEqual(x.chain_mint_payload.get("token_address"),x.token_address)\n        self.assertEqual(x.evidence_state,"INDEPENDENT_CHAIN_AND_PROVIDER_EVIDENCE_UNBLENDED"); self.assertFalse(x.execution_authority)\nif __name__=="__main__":\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] OAD-305 Solana launch/security evidence profile physically certified")\n'
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
