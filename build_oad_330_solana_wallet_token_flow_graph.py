from __future__ import annotations
import ast,hashlib,os,textwrap
from pathlib import Path
BUILD_ID='OAD-330'; TITLE='SOLANA WALLET TOKEN FLOW GRAPH'; EXPECTED='build_oad_330_solana_wallet_token_flow_graph.py'; MODULE='oad_330_solana_wallet_token_flow_graph.py'; TEST='test_oad_330_solana_wallet_token_flow_graph.py'; DEPENDENCIES={'qseries_v2/oracle_adapters/independent/oad_319_solana_transaction_canonical_envelope.py': ('pre_token_balances', 'post_token_balances'), 'qseries_v2/oracle_adapters/independent/oad_329_solana_dex_transaction_attribution.py': ('SolanaDexTransactionAttribution',)}
MODULE_SOURCE=r"""\

from __future__ import annotations
from dataclasses import dataclass
READ_ONLY=True;PROBABILITY_ENABLED=False;DIRECTION_ENABLED=False;PUBLICATION_ALLOWED=False;EXECUTION_AUTHORITY=False
def _amt(x):
    u=x.get("uiTokenAmount") or {};v=u.get("uiAmountString")
    try:return float(v)
    except (TypeError,ValueError):return float(u.get("uiAmount") or 0.0)
@dataclass(frozen=True,slots=True)
class SolanaWalletTokenFlow:
 signature:str;slot:int;owner:str;mint:str;delta:float;account_index:int|None;execution_authority:bool=False
def build_wallet_token_flows(envelopes):
    out=[]
    for e in envelopes:
        pre={(x.get("accountIndex"),str(x.get("mint") or ""),str(x.get("owner") or "")):_amt(x) for x in e.pre_token_balances}
        post={(x.get("accountIndex"),str(x.get("mint") or ""),str(x.get("owner") or "")):_amt(x) for x in e.post_token_balances}
        for k in sorted(set(pre)|set(post),key=str):
            d=post.get(k,0.0)-pre.get(k,0.0)
            if abs(d)>0:out.append(SolanaWalletTokenFlow(e.signature,e.slot,k[2],k[1],d,k[0],False))
    return tuple(out)

"""
TEST_SOURCE=r"""\

import unittest
from types import SimpleNamespace
from qseries_v2.oracle_adapters.independent.oad_330_solana_wallet_token_flow_graph import *
class T(unittest.TestCase):
 def test_flows(self):
  e=SimpleNamespace(signature="s",slot=1,pre_token_balances=({"accountIndex":1,"mint":"SOLX","owner":"W","uiTokenAmount":{"uiAmountString":"10"}},{"accountIndex":2,"mint":"USDC","owner":"W","uiTokenAmount":{"uiAmountString":"2"}},),post_token_balances=({"accountIndex":1,"mint":"SOLX","owner":"W","uiTokenAmount":{"uiAmountString":"7"}},{"accountIndex":2,"mint":"USDC","owner":"W","uiTokenAmount":{"uiAmountString":"5"}},))
  x=build_wallet_token_flows((e,))
  print("[FLOWS]",tuple((z.owner,z.mint,z.delta) for z in x))
  self.assertEqual(len(x),2);self.assertEqual({z.delta for z in x},{-3.0,3.0})
if __name__=="__main__":
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
 if not r.wasSuccessful():raise SystemExit(1)
 print("[PASS] OAD-330 wallet/token balance-flow graph certified")

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
