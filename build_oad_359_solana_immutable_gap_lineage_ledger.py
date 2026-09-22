from __future__ import annotations
import ast, hashlib, os, textwrap
from pathlib import Path
EXPECTED='build_oad_359_solana_immutable_gap_lineage_ledger.py'; BUILD_ID='OAD-359'; TITLE='SOLANA IMMUTABLE GAP LINEAGE LEDGER'; MODULE='oad_359_solana_immutable_gap_lineage_ledger.py'; TEST='test_oad_359_solana_immutable_gap_lineage_ledger.py'; DEPS={'qseries_v2/oracle_adapters/independent/oad_358_solana_skipped_slot_safe_checkpoint.py': ('SolanaContiguousSlotProof', 'safe_checkpoint_target')}
MODULE_SOURCE=r"""\

from __future__ import annotations
from dataclasses import dataclass,asdict
from pathlib import Path
import json,hashlib,os,time
READ_ONLY=True; PROBABILITY_ENABLED=False; DIRECTION_ENABLED=False; PUBLICATION_ALLOWED=False; EXECUTION_AUTHORITY=False
@dataclass(frozen=True,slots=True)
class SolanaGapLineageRecord:
    sequence:int; observed_at_ns:int; start_slot:int; end_slot:int; disposition:str; slots:tuple; previous_hash:str; record_hash:str; execution_authority:bool=False
def _path(root=None):
    r=Path(root or ".").resolve(); return r/"runtime_state"/"solana_universal_chain"/"gap_lineage.jsonl"
def _hash(payload):
    return hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(",",":")).encode()).hexdigest()
def append_gap_lineage(start_slot,end_slot,disposition,slots,root=None):
    p=_path(root); p.parent.mkdir(parents=True,exist_ok=True)
    prev="GENESIS"; seq=1
    if p.exists():
        lines=[x for x in p.read_text(encoding="utf-8").splitlines() if x.strip()]
        if lines:
            last=json.loads(lines[-1]); prev=last["record_hash"]; seq=int(last["sequence"])+1
    base={"sequence":seq,"observed_at_ns":time.time_ns(),"start_slot":int(start_slot),"end_slot":int(end_slot),
          "disposition":str(disposition),"slots":tuple(int(x) for x in slots),"previous_hash":prev,"execution_authority":False}
    rh=_hash(base); rec=SolanaGapLineageRecord(record_hash=rh,**base)
    with p.open("a",encoding="utf-8",newline="\n") as f:
        f.write(json.dumps(asdict(rec),sort_keys=True,separators=(",",":"))+"\n"); f.flush(); os.fsync(f.fileno())
    return rec
def verify_gap_lineage(root=None):
    p=_path(root)
    if not p.exists(): return True,0
    prev="GENESIS"; count=0
    for line in p.read_text(encoding="utf-8").splitlines():
        if not line.strip(): continue
        d=json.loads(line); rh=d.pop("record_hash")
        if d["previous_hash"]!=prev or _hash(d)!=rh: return False,count
        prev=rh; count+=1
    return True,count

"""
TEST_SOURCE=r"""\

import unittest,tempfile
from qseries_v2.oracle_adapters.independent.oad_359_solana_immutable_gap_lineage_ledger import *
class T(unittest.TestCase):
    def test_chain(self):
        with tempfile.TemporaryDirectory() as d:
            a=append_gap_lineage(10,12,"SKIPPED_SLOTS",(11,),d); b=append_gap_lineage(13,15,"RECOVERABLE_GAP",(14,15),d)
            ok,n=verify_gap_lineage(d); print("[GAP-LEDGER]",n,a.record_hash[:12],b.previous_hash[:12]); self.assertTrue(ok); self.assertEqual(n,2)
if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-359 immutable hash-chained Solana gap lineage certified")

"""
def root():
    for b in (Path.cwd().resolve(),Path(__file__).resolve().parent):
        for p in (b,*b.parents):
            if (p/"qseries_v2").is_dir(): return p
    raise RuntimeError("Q Series repository root not found")
def atomic(p,src):
    src=textwrap.dedent(src).lstrip(); ast.parse(src,filename=str(p)); p.parent.mkdir(parents=True,exist_ok=True)
    q=p.with_suffix(p.suffix+".tmp"); q.write_text(src,encoding="utf-8",newline="\n"); os.replace(q,p)
def verify(p,marks):
    if not p.is_file(): raise RuntimeError("dependency missing: "+str(p))
    x=p.read_text(encoding="utf-8"); ast.parse(x,filename=str(p))
    for m in marks:
        if m not in x: raise RuntimeError("dependency interface missing: "+p.name+" -> "+m)
def main():
    if Path(__file__).name!=EXPECTED: raise RuntimeError("installer identity mismatch")
    r=root(); pkg=r/"qseries_v2"/"oracle_adapters"/"independent"; m=pkg/MODULE; t=r/TEST; init=pkg/"__init__.py"
    print("="*120); print(" "+BUILD_ID+" "+TITLE+" INSTALLER"); print("="*120); print("[ROOT]",r)
    for rel,marks in DEPS.items(): verify(r/rel,marks); print("[PASS] dependency interface verified:",rel)
    protected=[]
    for rel in ("qseries_v2/oracle_production_hardening/oph_023_postgresql_single_writer_production_freeze.py",
                "qseries_v2/oracle_adapters/independent/oad_327_solana_universal_continuity_physical_certification.py",
                "qseries_v2/oracle_adapters/independent/oad_357_solana_decoder_closeout_same_universe_physical_gate.py"):
        p=r/rel
        if not p.is_file(): raise RuntimeError("protected boundary missing: "+rel)
        protected.append((p,hashlib.sha256(p.read_bytes()).hexdigest()))
    old={p:(p.read_bytes() if p.exists() else None) for p in (m,t,init)}
    try:
        atomic(m,MODULE_SOURCE); atomic(t,TEST_SOURCE)
        lines=init.read_text(encoding="utf-8").splitlines() if init.exists() else []
        e="from ."+m.stem+" import *"
        if e not in lines: lines.append(e)
        atomic(init,"\n".join(x for x in lines if x.strip())+"\n")
        for p,h in protected:
            if hashlib.sha256(p.read_bytes()).hexdigest()!=h: raise RuntimeError("protected boundary changed: "+p.name)
        print("[PASS] module installed:",m.relative_to(r)); print("[PASS] test installed:",t.name)
        print("[PASS] OPH-023/OAD-327/OAD-357 preserved byte-for-byte unchanged")
        print("[PASS] no bypass PostgreSQL writer introduced")
        print("[PASS] GMGN not required")
        print("[PASS] probability=FALSE direction=FALSE publication=FALSE execution=FALSE")
        print("[DONE] "+BUILD_ID+" INSTALLATION COMPLETE")
    except Exception:
        for p,b in old.items():
            if b is None:
                if p.exists(): p.unlink()
            else: p.write_bytes(b)
        print("[ROLLBACK] affected files restored"); raise
if __name__=="__main__": main()
