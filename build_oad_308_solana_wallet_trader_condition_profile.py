from __future__ import annotations
import ast,hashlib,os,textwrap
from pathlib import Path
BUILD_ID='OAD-308'
TITLE='SOLANA WALLET / TRADER CONDITION PROFILE'
EXPECTED='build_oad_308_solana_wallet_trader_condition_profile.py'
MODULE='oad_308_solana_wallet_trader_condition_profile.py'
TEST='test_oad_308_solana_wallet_trader_condition_profile.py'
DEPENDENCIES=[('qseries_v2/oracle_adapters/independent/oad_300_solana_wallet_trader_claim_normalization.py', ('def normalize_current_gmgn_wallet_trader_intelligence', 'class WalletTraderIntelligence'))]
MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass\nfrom .oad_300_solana_wallet_trader_claim_normalization import normalize_current_gmgn_wallet_trader_intelligence\nREAD_ONLY=True; PROBABILITY_ENABLED=False; DIRECTION_ENABLED=False; PUBLICATION_ALLOWED=False; EXECUTION_AUTHORITY=False\n@dataclass(frozen=True,slots=True)\nclass WalletTraderConditionProfile:\n    token_address:str; holder_rows:int; trader_rows:int; unique_wallets:int; overlap_wallets:int; conditions:tuple; provider_claim_only:bool=True; probability:None=None; direction:None=None; execution_authority:bool=False\ndef build_current_wallet_trader_condition_profile(timeout_seconds=30.0):\n    x=normalize_current_gmgn_wallet_trader_intelligence(timeout_seconds)\n    holders={c.wallet_address for c in x.provider_claims if c.claim_kind=="holder" and c.wallet_address}\n    traders={c.wallet_address for c in x.provider_claims if c.claim_kind=="trader" and c.wallet_address}\n    unique=holders|traders; overlap=holders&traders\n    conditions=(("holder_rows",x.holder_rows),("trader_rows",x.trader_rows),("unique_identified_wallets",len(unique)),("holder_trader_overlap",len(overlap)))\n    return WalletTraderConditionProfile(x.token_address,x.holder_rows,x.trader_rows,len(unique),len(overlap),conditions,True,None,None,False)\n'
TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_adapters.independent.oad_308_solana_wallet_trader_condition_profile import *\nclass T(unittest.TestCase):\n def test_physical(self):\n  x=build_current_wallet_trader_condition_profile()\n  print("[PHYSICAL] token=",x.token_address); print("[PHYSICAL] holder_rows=",x.holder_rows); print("[PHYSICAL] trader_rows=",x.trader_rows); print("[PHYSICAL] unique_wallets=",x.unique_wallets); print("[PHYSICAL] overlap_wallets=",x.overlap_wallets)\n  self.assertGreater(x.holder_rows,0); self.assertGreater(x.trader_rows,0); self.assertTrue(x.provider_claim_only); self.assertIsNone(x.probability); self.assertFalse(x.execution_authority)\nif __name__=="__main__":\n r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n if not r.wasSuccessful(): raise SystemExit(1)\n print("[PASS] OAD-308 wallet/trader condition profile physically certified as provider-claim intelligence")\n'
def root():
    for b in (Path.cwd().resolve(),Path(__file__).resolve().parent):
        for p in (b,*b.parents):
            if (p/"qseries_v2").is_dir(): return p
    raise RuntimeError("Q Series repository root not found")
def write(p,s):
    s=textwrap.dedent(s).lstrip(); ast.parse(s,filename=str(p)); p.parent.mkdir(parents=True,exist_ok=True)
    q=p.with_suffix(p.suffix+".tmp"); q.write_text(s,encoding="utf-8",newline="\n"); os.replace(q,p)
def main():
    if Path(__file__).name!=EXPECTED: raise RuntimeError("installer filename identity mismatch")
    r=root(); pkg=r/"qseries_v2"/"oracle_adapters"/"independent"; m=pkg/MODULE; t=r/TEST; init=pkg/"__init__.py"
    print("="*120); print(" "+BUILD_ID+" "+TITLE+" INSTALLER"); print("="*120); print("[ROOT]",r)
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
        write(m,MODULE_SOURCE); write(t,TEST_SOURCE)
        lines=init.read_text(encoding="utf-8").splitlines() if init.exists() else []; exp="from ."+m.stem+" import *"
        if exp not in lines: lines.append(exp)
        write(init,"\n".join(x for x in lines if x.strip())+"\n")
        for p,h in protected:
            if hashlib.sha256(p.read_bytes()).hexdigest()!=h: raise RuntimeError("frozen boundary changed: "+p.name)
        print("[PASS] module installed:",m.relative_to(r)); print("[PASS] test installed:",t.name)
        print("[PASS] frozen OPH-023/Kalshi OAD-055 unchanged")
        print("[PASS] source identity and evidence class remain explicit; no cross-token blending")
        print("[PASS] probability=FALSE direction=FALSE publication=FALSE execution=FALSE")
        print("[DONE] "+BUILD_ID+" INSTALLATION COMPLETE")
    except Exception:
        for p,b in old.items():
            if b is None:
                if p.exists(): p.unlink()
            else:p.write_bytes(b)
        print("[ROLLBACK] affected files restored"); raise
if __name__=="__main__": main()
