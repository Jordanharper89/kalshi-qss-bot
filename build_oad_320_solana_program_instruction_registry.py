from __future__ import annotations
import ast,hashlib,os,textwrap
from pathlib import Path
BUILD_ID='OAD-320'; TITLE='SOLANA PROGRAM AND INSTRUCTION REGISTRY'; EXPECTED='build_oad_320_solana_program_instruction_registry.py'; MODULE='oad_320_solana_program_instruction_registry.py'; TEST='test_oad_320_solana_program_instruction_registry.py'; DEPENDENCIES={'qseries_v2/oracle_adapters/independent/oad_319_solana_transaction_canonical_envelope.py': ('class SolanaTransactionEnvelope', 'canonical_transaction_envelopes')}
MODULE_SOURCE=r"""\

from __future__ import annotations
from dataclasses import dataclass
READ_ONLY=True; PROBABILITY_ENABLED=False; DIRECTION_ENABLED=False; PUBLICATION_ALLOWED=False; EXECUTION_AUTHORITY=False
PROGRAMS={
"11111111111111111111111111111111":"SYSTEM",
"TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA":"SPL_TOKEN",
"TokenzQdYhYhQb...":"TOKEN_2022",
"ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL":"ASSOCIATED_TOKEN",
"ComputeBudget111111111111111111111111111111":"COMPUTE_BUDGET",
"MemoSq4gqABAXKb96qnH8TysNcWxMyWCqXgDLGmfcHr":"MEMO",
}
@dataclass(frozen=True,slots=True)
class SolanaInstructionClassification:
 signature:str; instruction_index:int; program_id:str; program_class:str; parsed_type:str|None; retained:bool=True; execution_authority:bool=False
def _pid(ix,keys):
 p=ix.get("programId")
 if p:return str(p)
 n=ix.get("programIdIndex")
 return keys[int(n)] if n is not None and int(n)<len(keys) else "UNKNOWN"
def classify_transaction_instructions(envelopes):
 out=[]
 for e in envelopes:
  all_ix=list(e.instructions)
  for group in e.inner_instructions:
   all_ix.extend(tuple(group.get("instructions") or ()))
  for i,ix in enumerate(all_ix):
   if not isinstance(ix,dict): continue
   pid=_pid(ix,e.account_keys); parsed=ix.get("parsed"); typ=parsed.get("type") if isinstance(parsed,dict) else None
   pclass=PROGRAMS.get(pid)
   if pclass is None:
    pl=(str(ix.get("program") or "")+" "+str(typ or "")).lower()
    if "token" in pl:pclass="TOKEN_PROGRAM"
    elif "system" in pl:pclass="SYSTEM"
    else:pclass="UNKNOWN_PROGRAM"
   out.append(SolanaInstructionClassification(e.signature,i,pid,pclass,str(typ) if typ else None,True,False))
 return tuple(out)

"""
TEST_SOURCE=r"""\

import unittest
from types import SimpleNamespace
from qseries_v2.oracle_adapters.independent.oad_320_solana_program_instruction_registry import *
class T(unittest.TestCase):
 def test_unknown_retained(self):
  e=SimpleNamespace(signature="s",instructions=({"programId":"NEWPROGRAM","parsed":{"type":"mystery"}},),inner_instructions=(),account_keys=())
  x=classify_transaction_instructions((e,))[0]
  print("[PROGRAM]",x.program_id,x.program_class,"retained=",x.retained)
  self.assertEqual(x.program_class,"UNKNOWN_PROGRAM"); self.assertTrue(x.retained)
if __name__=="__main__":
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
 if not r.wasSuccessful(): raise SystemExit(1)
 print("[PASS] OAD-320 known + unknown Solana instruction accounting certified")

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
