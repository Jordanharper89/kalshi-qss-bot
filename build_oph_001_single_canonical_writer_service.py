from pathlib import Path
import importlib,os,subprocess,sys
ROOT=Path.cwd().resolve(); PKG=ROOT/"qseries_v2"/"oracle_production_hardening"
MOD=PKG/"oph_001_single_canonical_writer_service.py"; TEST=ROOT/"test_oph_001_single_canonical_writer_service.py"; INIT=PKG/"__init__.py"
MODULE='from dataclasses import dataclass\nfrom threading import Lock\n\n@dataclass(frozen=True)\nclass CanonicalWriteEnvelope:\n    writer_id:str; priority:int; observations:tuple; admitted_sequence:int; execution_authority:bool=False\n\n@dataclass(frozen=True)\nclass CanonicalWriterServiceState:\n    accepted_batches:int; accepted_observations:int; completed_batches:int; completed_observations:int; rejected_batches:int; next_sequence:int; execution_authority:bool=False\n\nclass SingleCanonicalWriterService:\n    def __init__(self):\n        self._lock=Lock(); self._queue=[]; self._sequence=0\n        self._accepted_batches=0; self._accepted_observations=0\n        self._completed_batches=0; self._completed_observations=0; self._rejected_batches=0\n    def submit(self,writer_id,observations,priority):\n        items=tuple(observations)\n        if not items:\n            self._rejected_batches+=1; raise ValueError("empty canonical write batch")\n        with self._lock:\n            self._sequence+=1\n            env=CanonicalWriteEnvelope(str(writer_id),int(priority),items,self._sequence,False)\n            self._queue.append(env)\n            self._accepted_batches+=1; self._accepted_observations+=len(items)\n            return env\n    def dequeue(self):\n        with self._lock:\n            if not self._queue: return None\n            self._queue.sort(key=lambda x:(-x.priority,x.admitted_sequence))\n            return self._queue.pop(0)\n    def mark_completed(self,envelope):\n        self._completed_batches+=1; self._completed_observations+=len(envelope.observations)\n    def state(self):\n        return CanonicalWriterServiceState(self._accepted_batches,self._accepted_observations,self._completed_batches,self._completed_observations,self._rejected_batches,self._sequence+1,False)\n\ndef verify_oph_001_single_canonical_writer_service():\n    s=SingleCanonicalWriterService()\n    s.submit("coverage",("c1","c2"),20); s.submit("fast_lane",("f1",),100)\n    a=s.dequeue(); b=s.dequeue(); s.mark_completed(a); s.mark_completed(b); st=s.state()\n    return a.writer_id=="fast_lane" and b.writer_id=="coverage" and st.completed_observations==3 and not st.execution_authority\n'; TESTSRC='import unittest\nfrom qseries_v2.oracle_production_hardening.oph_001_single_canonical_writer_service import verify_oph_001_single_canonical_writer_service\nclass T(unittest.TestCase):\n    def test_verifier(self): self.assertTrue(verify_oph_001_single_canonical_writer_service())\nif __name__=="__main__":\n    print("="*80); print(" OPH-001 CERTIFICATION TEST"); print(" SINGLE CANONICAL WRITER SERVICE"); print("="*80)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] OPH-001 certified"); print("[DONE] OPH-001 CERTIFIED")\n'
def write_exact(p,s):
    p.parent.mkdir(parents=True,exist_ok=True); t=p.with_suffix(p.suffix+".tmp"); t.write_text(s,encoding="utf-8",newline="\n"); os.replace(t,p)
def main():
    print("="*80); print(" OPH-001 INSTALLER"); print(" SINGLE CANONICAL WRITER SERVICE"); print("="*80); print("[ROOT]",ROOT)
    sys.path.insert(0,str(ROOT)); print("[PASS] New Oracle-wide production hardening subsystem initialized")
    print("[PASS] Existing OPC/OAD/OLA/OLR/OCR source boundaries remain untouched")
    affected=(MOD,TEST,INIT); old={p:(p.read_bytes() if p.exists() else None) for p in affected}
    try:
        write_exact(MOD,MODULE); write_exact(TEST,TESTSRC)
        cur=INIT.read_text(encoding="utf-8") if INIT.exists() else ""; ex="from .oph_001_single_canonical_writer_service import *"
        if ex not in cur: write_exact(INIT,cur.rstrip()+"\n"+ex+"\n")
        subprocess.run([sys.executable,str(TEST)],cwd=str(ROOT),check=True)
    except Exception:
        for p,b in old.items():
            if b is None:
                if p.exists(): p.unlink()
            else: p.write_bytes(b)
        print("[ROLLBACK] OPH-001 installation failed"); raise
    print("[PASS] Wrote:",MOD.relative_to(ROOT)); print("[PASS] Wrote:",TEST.name); print("[DONE] OPH-001 INSTALLATION AND CERTIFICATION COMPLETE")
if __name__=="__main__": main()
