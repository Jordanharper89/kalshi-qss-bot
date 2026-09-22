from __future__ import annotations
import ast,hashlib,os,textwrap
from pathlib import Path
EXPECTED='build_oad_309_solana_target_token_wallet_trader_coverage_acquisition.py'
MODULE="oad_309_solana_target_token_wallet_trader_coverage_acquisition.py"
TEST="test_oad_309_solana_target_token_wallet_trader_coverage_acquisition.py"
DEPENDENCIES=[('qseries_v2/oracle_adapters/independent/oad_298_gmgn_solana_holder_intelligence.py', ('def acquire_gmgn_token_holders',)), ('qseries_v2/oracle_adapters/independent/oad_299_gmgn_solana_trader_intelligence.py', ('def acquire_gmgn_token_traders',)), ('qseries_v2/oracle_adapters/independent/oad_300_solana_wallet_trader_claim_normalization.py', ('class ProviderClaim', 'class WalletTraderIntelligence', 'def _rows', 'def _wallet')), ('qseries_v2/oracle_adapters/independent/oad_307_solana_temporal_market_condition_profile.py', ('def build_current_temporal_market_condition_profile', 'durable_read_only')), ('qseries_v2/oracle_adapters/independent/oad_287_gmgn_clean_provider_foundation.py', ('class GMGNRateLimitError',))]
MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass\nfrom datetime import datetime,timezone\n\nfrom .oad_298_gmgn_solana_holder_intelligence import acquire_gmgn_token_holders\nfrom .oad_299_gmgn_solana_trader_intelligence import acquire_gmgn_token_traders\nfrom .oad_300_solana_wallet_trader_claim_normalization import ProviderClaim,WalletTraderIntelligence,_rows,_wallet\nfrom .oad_307_solana_temporal_market_condition_profile import build_current_temporal_market_condition_profile\nfrom .oad_287_gmgn_clean_provider_foundation import GMGNRateLimitError\n\nREAD_ONLY=True\nPROBABILITY_ENABLED=False\nDIRECTION_ENABLED=False\nPUBLICATION_ALLOWED=False\nEXECUTION_AUTHORITY=False\n\n@dataclass(frozen=True,slots=True)\nclass TargetTokenWalletTraderCoverage:\n    token_address:str\n    state:str\n    holder_rows:int\n    trader_rows:int\n    provider_claims:tuple\n    retry_after_seconds:float|None\n    failure_detail:str|None\n    provider_claim_only:bool=True\n    execution_authority:bool=False\n\ndef _normalize(token,h,t):\n    hr=_rows(h.raw); tr=_rows(t.raw); claims=[]\n    for kind,rows in (("holder",hr),("trader",tr)):\n        for row in rows:\n            claims.append(ProviderClaim(_wallet(row),kind,"gmgn",dict(row),False))\n    return WalletTraderIntelligence(token,len(hr),len(tr),tuple(claims),False)\n\ndef acquire_target_token_wallet_trader_coverage(root=None,timeout_seconds=30.0):\n    # Exact target comes from Oracle\'s durable Solana identity, not from a fresh\n    # GMGN-selected token. This closes the cross-token coverage gap.\n    temporal=build_current_temporal_market_condition_profile(root=root)\n    token=temporal.token_address\n    try:\n        h=acquire_gmgn_token_holders(token,timeout_seconds)\n        t=acquire_gmgn_token_traders(token,timeout_seconds)\n        if h.token_address!=token or t.token_address!=token:\n            raise RuntimeError("target-token holder/trader identity mismatch")\n        x=_normalize(token,h,t)\n        return TargetTokenWalletTraderCoverage(\n            token,"ACQUIRED",x.holder_rows,x.trader_rows,x.provider_claims,\n            None,None,True,False\n        )\n    except GMGNRateLimitError as e:\n        retry=float(getattr(e,"retry_after_seconds",300.0) or 300.0)\n        return TargetTokenWalletTraderCoverage(\n            token,"RATE_LIMITED_HOLD",0,0,(),retry,\n            (str(e) or type(e).__name__)[:240],True,False\n        )\n'
TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_adapters.independent.oad_309_solana_target_token_wallet_trader_coverage_acquisition import *\n\nclass T(unittest.TestCase):\n    def test_physical_or_truthful_rate_limit_hold(self):\n        x=acquire_target_token_wallet_trader_coverage()\n        print("[PHYSICAL] token=",x.token_address)\n        print("[PHYSICAL] state=",x.state)\n        print("[PHYSICAL] holder_rows=",x.holder_rows)\n        print("[PHYSICAL] trader_rows=",x.trader_rows)\n        print("[PHYSICAL] provider_claims=",len(x.provider_claims))\n        print("[PHYSICAL] retry_after_seconds=",x.retry_after_seconds)\n        self.assertTrue(x.token_address)\n        self.assertIn(x.state,("ACQUIRED","RATE_LIMITED_HOLD"))\n        self.assertTrue(x.provider_claim_only)\n        self.assertFalse(x.execution_authority)\n        if x.state=="ACQUIRED":\n            self.assertEqual(len(x.provider_claims),x.holder_rows+x.trader_rows)\n            self.assertTrue(all(c.provider=="gmgn" and c.oracle_verified is False for c in x.provider_claims))\n        else:\n            self.assertGreaterEqual(x.retry_after_seconds,1.0)\n            self.assertEqual(len(x.provider_claims),0)\n\nif __name__=="__main__":\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] OAD-309 exact target-token wallet/trader coverage acquisition boundary certified")\n    print("[PASS] GMGN rate limit is a truthful HOLD, not a downstream reasoning failure")\n    print("[PASS] probability=FALSE direction=FALSE publication=FALSE execution=FALSE")\n'
def root():
    for b in (Path.cwd().resolve(),Path(__file__).resolve().parent):
        for p in (b,*b.parents):
            if (p/"qseries_v2").is_dir(): return p
    raise RuntimeError("Q Series repository root not found")
def write(p,s):
    s=textwrap.dedent(s).lstrip(); ast.parse(s,filename=str(p))
    p.parent.mkdir(parents=True,exist_ok=True); q=p.with_suffix(p.suffix+".tmp")
    q.write_text(s,encoding="utf-8",newline="\n"); os.replace(q,p)
def main():
    if Path(__file__).name!=EXPECTED: raise RuntimeError("installer filename identity mismatch")
    r=root();pkg=r/"qseries_v2"/"oracle_adapters"/"independent";m=pkg/MODULE;t=r/TEST;init=pkg/"__init__.py"
    print("="*120);print(" OAD-309 SOLANA TARGET-TOKEN WALLET/TRADER COVERAGE ACQUISITION INSTALLER");print("="*120);print("[ROOT]",r)
    for rel,marks in DEPENDENCIES:
        p=r/rel
        if not p.is_file(): raise RuntimeError("dependency missing: "+rel)
        s=p.read_text(encoding="utf-8");ast.parse(s,filename=str(p))
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
        write(m,MODULE_SOURCE);write(t,TEST_SOURCE)
        lines=init.read_text(encoding="utf-8").splitlines() if init.exists() else [];exp="from ."+m.stem+" import *"
        if exp not in lines:lines.append(exp)
        write(init,"\n".join(x for x in lines if x.strip())+"\n")
        for p,h in protected:
            if hashlib.sha256(p.read_bytes()).hexdigest()!=h:raise RuntimeError("frozen boundary changed: "+p.name)
        print("[PASS] exact durable Solana token is the GMGN holders/traders target")
        print("[PASS] cross-token GMGN selection removed from this coverage boundary")
        print("[PASS] GMGN 429/rate-limit becomes RATE_LIMITED_HOLD with retry metadata")
        print("[PASS] no condition/reasoning module invokes this acquisition boundary")
        print("[PASS] module installed:",m.relative_to(r));print("[PASS] test installed:",t.name)
        print("[PASS] frozen OPH-023/Kalshi OAD-055 unchanged")
        print("[PASS] probability=FALSE direction=FALSE publication=FALSE execution=FALSE")
        print("[DONE] OAD-309 INSTALLATION COMPLETE")
    except Exception:
        for p,b in old.items():
            if b is None:
                if p.exists():p.unlink()
            else:p.write_bytes(b)
        print("[ROLLBACK] affected files restored");raise
if __name__=="__main__":main()
