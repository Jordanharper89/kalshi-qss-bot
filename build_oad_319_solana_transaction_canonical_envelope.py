from __future__ import annotations
import ast,hashlib,os,textwrap
from pathlib import Path
BUILD_ID='OAD-319'; TITLE='SOLANA TRANSACTION CANONICAL ENVELOPE'; EXPECTED='build_oad_319_solana_transaction_canonical_envelope.py'; MODULE='oad_319_solana_transaction_canonical_envelope.py'; TEST='test_oad_319_solana_transaction_canonical_envelope.py'; DEPENDENCIES={'qseries_v2/oracle_adapters/independent/oad_318_solana_native_finalized_block_stream.py': ('class SolanaFinalizedBlockBatch', 'def acquire_finalized_block_batch')}
MODULE_SOURCE=r"""\

from __future__ import annotations
from dataclasses import dataclass
READ_ONLY=True; PROBABILITY_ENABLED=False; DIRECTION_ENABLED=False; PUBLICATION_ALLOWED=False; EXECUTION_AUTHORITY=False
@dataclass(frozen=True,slots=True)
class SolanaTransactionEnvelope:
 slot:int; block_time:int|None; blockhash:str; signature:str; version:object; success:bool; fee:int
 account_keys:tuple; instructions:tuple; inner_instructions:tuple; pre_token_balances:tuple; post_token_balances:tuple
 log_messages:tuple; raw_transaction:dict; execution_authority:bool=False
def _keys(msg):
 out=[]
 for x in tuple(msg.get("accountKeys") or ()):
  out.append(str(x.get("pubkey")) if isinstance(x,dict) else str(x))
 return tuple(out)
def canonical_transaction_envelopes(batch):
 out=[]
 for slot,b in batch.blocks:
  for row in tuple(b.get("transactions") or ()):
   tx=dict(row.get("transaction") or {}); meta=dict(row.get("meta") or {}); msg=dict(tx.get("message") or {})
   sigs=tuple(tx.get("signatures") or ())
   if not sigs: continue
   out.append(SolanaTransactionEnvelope(int(slot),b.get("blockTime"),str(b.get("blockhash") or ""),str(sigs[0]),row.get("version","legacy"),meta.get("err") is None,int(meta.get("fee") or 0),_keys(msg),tuple(msg.get("instructions") or ()),tuple(meta.get("innerInstructions") or ()),tuple(meta.get("preTokenBalances") or ()),tuple(meta.get("postTokenBalances") or ()),tuple(meta.get("logMessages") or ()),row,False))
 return tuple(out)

"""
TEST_SOURCE=r"""\

import unittest
from types import SimpleNamespace
from qseries_v2.oracle_adapters.independent.oad_319_solana_transaction_canonical_envelope import *
class T(unittest.TestCase):
 def test_envelope(self):
  b=SimpleNamespace(blocks=((7,{"blockTime":1,"blockhash":"h","transactions":[{"version":0,"transaction":{"signatures":["sig"],"message":{"accountKeys":[{"pubkey":"A"}],"instructions":[{"programId":"P"}]}},"meta":{"err":None,"fee":5000,"innerInstructions":[],"preTokenBalances":[],"postTokenBalances":[],"logMessages":["ok"]}}]}),))
  x=canonical_transaction_envelopes(b)[0]
  print("[TX]",x.signature,x.slot,x.success,x.account_keys)
  self.assertEqual(x.signature,"sig"); self.assertTrue(x.success)
if __name__=="__main__":
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
 if not r.wasSuccessful(): raise SystemExit(1)
 print("[PASS] OAD-319 full transaction canonical envelope certified")

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
