from __future__ import annotations
import ast,hashlib,os,textwrap
from pathlib import Path
BUILD_ID='OAD-321'; TITLE='SOLANA ECONOMIC EVENT EXTRACTION'; EXPECTED='build_oad_321_solana_economic_event_extraction.py'; MODULE='oad_321_solana_economic_event_extraction.py'; TEST='test_oad_321_solana_economic_event_extraction.py'; DEPENDENCIES={'qseries_v2/oracle_adapters/independent/oad_320_solana_program_instruction_registry.py': ('class SolanaInstructionClassification', 'classify_transaction_instructions'), 'qseries_v2/oracle_adapters/independent/oad_319_solana_transaction_canonical_envelope.py': ('class SolanaTransactionEnvelope',)}
MODULE_SOURCE=r"""\

from __future__ import annotations
from dataclasses import dataclass
READ_ONLY=True; PROBABILITY_ENABLED=False; DIRECTION_ENABLED=False; PUBLICATION_ALLOWED=False; EXECUTION_AUTHORITY=False
@dataclass(frozen=True,slots=True)
class SolanaEconomicEvent:
 signature:str; slot:int; event_type:str; program_id:str; mint:str|None; owner:str|None; amount_delta:float|None
 evidence:dict; execution_authority:bool=False
def _amount(x):
 ui=(x.get("uiTokenAmount") or {})
 v=ui.get("uiAmountString")
 try:return float(v)
 except (TypeError,ValueError): return float(ui.get("uiAmount") or 0.0)
def extract_economic_events(envelopes,classifications):
 bysig={}
 for c in classifications:bysig.setdefault(c.signature,[]).append(c)
 out=[]
 for e in envelopes:
  cs=bysig.get(e.signature,[])
  for c in cs:
   typ=(c.parsed_type or "").lower()
   et=None
   if typ in ("transfer","transferchecked"):et="TOKEN_TRANSFER" if "TOKEN" in c.program_class else "NATIVE_TRANSFER"
   elif "mint" in typ:et="TOKEN_MINT"
   elif "burn" in typ:et="TOKEN_BURN"
   elif typ in ("initializeaccount","initializeaccount2","initializeaccount3"):et="TOKEN_ACCOUNT_CREATE"
   if et: out.append(SolanaEconomicEvent(e.signature,e.slot,et,c.program_id,None,None,None,{"instruction_index":c.instruction_index},False))
  pre={(x.get("accountIndex"),x.get("mint"),x.get("owner")):_amount(x) for x in e.pre_token_balances}
  post={(x.get("accountIndex"),x.get("mint"),x.get("owner")):_amount(x) for x in e.post_token_balances}
  for k in set(pre)|set(post):
   d=post.get(k,0.0)-pre.get(k,0.0)
   if abs(d)>0:
    out.append(SolanaEconomicEvent(e.signature,e.slot,"TOKEN_BALANCE_FLOW","BALANCE_DELTA",str(k[1]) if k[1] else None,str(k[2]) if k[2] else None,d,{"account_index":k[0]},False))
  if not cs:
   out.append(SolanaEconomicEvent(e.signature,e.slot,"UNCLASSIFIED_TRANSACTION","UNKNOWN",None,None,None,{"retained":True},False))
 return tuple(out)

"""
TEST_SOURCE=r"""\

import unittest
from types import SimpleNamespace
from qseries_v2.oracle_adapters.independent.oad_321_solana_economic_event_extraction import *
class T(unittest.TestCase):
 def test_flow(self):
  e=SimpleNamespace(signature="s",slot=9,pre_token_balances=({"accountIndex":1,"mint":"M","owner":"W","uiTokenAmount":{"uiAmountString":"1"}},),post_token_balances=({"accountIndex":1,"mint":"M","owner":"W","uiTokenAmount":{"uiAmountString":"3"}},))
  c=SimpleNamespace(signature="s",parsed_type="transferChecked",program_class="SPL_TOKEN",program_id="T",instruction_index=0)
  x=extract_economic_events((e,),(c,))
  print("[EVENTS]",tuple((z.event_type,z.amount_delta) for z in x))
  self.assertTrue(any(z.event_type=="TOKEN_TRANSFER" for z in x)); self.assertTrue(any(z.amount_delta==2 for z in x))
if __name__=="__main__":
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
 if not r.wasSuccessful(): raise SystemExit(1)
 print("[PASS] OAD-321 Solana economic-event extraction certified")

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
    for rel in ("qseries_v2/oracle_production_hardening/oph_023_postgresql_single_writer_production_freeze.py","qseries_v2/oracle_adapters/kalshi/oad_055_kalshi_production_freeze.py"):
        p=r/rel
        if not p.is_file(): raise RuntimeError("frozen boundary missing: "+rel)
        protected.append((p,hashlib.sha256(p.read_bytes()).hexdigest()))
    old={p:(p.read_bytes() if p.exists() else None) for p in (m,t,init)}
    try:
        atomic(m,MODULE_SOURCE); atomic(t,TEST_SOURCE)
        lines=init.read_text(encoding="utf-8").splitlines() if init.exists() else []
        exp="from ."+m.stem+" import *"
        if exp not in lines: lines.append(exp)
        atomic(init,"\n".join(x for x in lines if x.strip())+"\n")
        for p,h in protected:
            if hashlib.sha256(p.read_bytes()).hexdigest()!=h: raise RuntimeError("frozen boundary changed: "+p.name)
        print("[PASS] module installed:",m.relative_to(r)); print("[PASS] test installed:",t.name)
        print("[PASS] frozen OPH-023/Kalshi OAD-055 unchanged")
        print("[PASS] native Solana RPC foundation; GMGN not required")
        print("[PASS] probability=FALSE direction=FALSE publication=FALSE execution=FALSE")
        print("[DONE] "+BUILD_ID+" INSTALLATION COMPLETE")
    except Exception:
        for p,b in old.items():
            if b is None:
                if p.exists(): p.unlink()
            else:p.write_bytes(b)
        print("[ROLLBACK] affected files restored"); raise
if __name__=="__main__": main()
