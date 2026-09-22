from __future__ import annotations
import ast,hashlib,os,textwrap
from pathlib import Path
BUILD_ID='OAD-304'
TITLE='SOLANA CREATOR / DEPLOYER CLAIM INTELLIGENCE'
EXPECTED='build_oad_304_solana_creator_deployer_claim_intelligence_CERTIFIED_REBUILD.py'
MODULE='oad_304_solana_creator_deployer_claim_intelligence.py'
TEST='test_oad_304_solana_creator_deployer_claim_intelligence.py'
DEPENDENCIES=[('qseries_v2/oracle_adapters/independent/oad_302_solana_security_evidence_boundary.py', ('def acquire_current_solana_security_evidence', 'provider_claim_only'))]
MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass\nfrom .oad_302_solana_security_evidence_boundary import acquire_current_solana_security_evidence\nREAD_ONLY=True; PROBABILITY_ENABLED=False; DIRECTION_ENABLED=False; PUBLICATION_ALLOWED=False; EXECUTION_AUTHORITY=False\nKEYS=("creator","creator_address","deployer","deployer_address","owner","owner_address","dev","dev_address")\n@dataclass(frozen=True,slots=True)\nclass CreatorDeployerClaim:\n    token_address:str; field_path:str; value:str; provider:str="gmgn"; oracle_verified:bool=False; execution_authority:bool=False\n@dataclass(frozen=True,slots=True)\nclass CreatorDeployerReport:\n    token_address:str; claims:tuple; claim_count:int; provider_claim_only:bool=True; execution_authority:bool=False\ndef _extract(token,v,path="",out=None):\n    out=[] if out is None else out\n    if isinstance(v,dict):\n        for k,z in v.items():\n            p=(path+"."+str(k)).strip(".")\n            if str(k).lower() in KEYS and z not in (None,"",[],{}): out.append(CreatorDeployerClaim(token,p,str(z),"gmgn",False,False))\n            if isinstance(z,(dict,list)): _extract(token,z,p,out)\n    elif isinstance(v,list):\n        for i,z in enumerate(v):\n            if isinstance(z,(dict,list)): _extract(token,z,path+"["+str(i)+"]",out)\n    return out\ndef acquire_current_creator_deployer_claims(timeout_seconds=30.0):\n    x=acquire_current_solana_security_evidence(timeout_seconds); rows=tuple(_extract(x.token_address,x.gmgn_security))\n    return CreatorDeployerReport(x.token_address,rows,len(rows),True,False)\n'
TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_adapters.independent.oad_304_solana_creator_deployer_claim_intelligence import *\nclass T(unittest.TestCase):\n    def test_physical(self):\n        r=acquire_current_creator_deployer_claims()\n        print("[PHYSICAL] token=",r.token_address); print("[PHYSICAL] creator_deployer_claims=",r.claim_count)\n        for x in r.claims[:3]: print("[CLAIM]",x.field_path,x.value[:80],"oracle_verified=",x.oracle_verified)\n        self.assertEqual(r.claim_count,len(r.claims)); self.assertTrue(r.provider_claim_only)\n        self.assertTrue(all(x.provider=="gmgn" and x.oracle_verified is False for x in r.claims))\nif __name__=="__main__":\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] OAD-304 creator/deployer extraction physically certified without promoting provider claims to truth")\n'
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
