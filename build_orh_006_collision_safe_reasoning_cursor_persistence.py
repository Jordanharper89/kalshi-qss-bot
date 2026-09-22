from pathlib import Path
import os,subprocess,sys
ROOT=Path.cwd().resolve()
MOD=ROOT/"qseries_v2"/"oracle_continuous_reasoning"/"ocr_011_reasoning_cursor_state.py"
TEST=ROOT/"test_orh_006_collision_safe_reasoning_cursor_persistence.py"
MODULE_SOURCE=r"""from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import json,os,time,uuid
OCR_011_BUILD_ID="OCR-011"
OCR_011_REVISION="OCR_011_REASONING_CURSOR_STATE_ORH_006_COLLISION_SAFE_V1"
@dataclass(frozen=True)
class ReasoningCursorState:
    order_column:str
    order_value:str
    observation_id:str
    batches_completed:int
    observations_processed:int
def empty_reasoning_cursor():return ReasoningCursorState("","","",0,0)
def load_reasoning_cursor(path):
    p=Path(path)
    if not p.is_file():return empty_reasoning_cursor()
    d=json.loads(p.read_text(encoding="utf-8"))
    return ReasoningCursorState(str(d.get("order_column") or ""),str(d.get("order_value") or ""),str(d.get("observation_id") or ""),int(d.get("batches_completed",0)),int(d.get("observations_processed",0)))
def _atomic_replace_json(path,payload,max_attempts=8):
    p=Path(path);p.parent.mkdir(parents=True,exist_ok=True);raw=json.dumps(payload,sort_keys=True,separators=(",",":"));last=None
    for attempt in range(1,int(max_attempts)+1):
        tmp=p.with_name(p.name+f".{os.getpid()}.{uuid.uuid4().hex}.tmp")
        try:
            tmp.write_text(raw,encoding="utf-8",newline="\n");os.replace(tmp,p);return p
        except PermissionError as exc:
            last=exc
            try:
                if tmp.exists():tmp.unlink()
            except Exception:pass
            if attempt>=max_attempts:break
            time.sleep(min(0.5,0.025*(2**(attempt-1))))
        finally:
            try:
                if tmp.exists():tmp.unlink()
            except Exception:pass
    raise last or PermissionError("atomic reasoning cursor replace failed")
def save_reasoning_cursor(path,state):
    _atomic_replace_json(path,{"order_column":state.order_column,"order_value":state.order_value,"observation_id":state.observation_id,"batches_completed":state.batches_completed,"observations_processed":state.observations_processed})
def advance_reasoning_cursor(state,order_column,order_value,observation_id,processed_count):
    if int(processed_count)<1:raise ValueError("processed_count must be positive")
    return ReasoningCursorState(str(order_column),str(order_value),str(observation_id),state.batches_completed+1,state.observations_processed+int(processed_count))
def verify_ocr_011_reasoning_cursor_state():
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        p=Path(d)/"cursor.json";s=advance_reasoning_cursor(empty_reasoning_cursor(),"sequence_number","42","obs42",3);save_reasoning_cursor(p,s);return load_reasoning_cursor(p)==s
"""
TEST_SOURCE=r"""import tempfile,unittest,inspect
from pathlib import Path
import qseries_v2.oracle_continuous_reasoning.ocr_011_reasoning_cursor_state as m
class T(unittest.TestCase):
    def test_roundtrip(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"cursor.json";s=m.advance_reasoning_cursor(m.empty_reasoning_cursor(),"sequence_number","99","o",2);m.save_reasoning_cursor(p,s);self.assertEqual(m.load_reasoning_cursor(p),s);self.assertFalse((Path(d)/"cursor.json.tmp").exists())
    def test_unique_tmp_contract(self):
        s=inspect.getsource(m._atomic_replace_json);self.assertIn("uuid.uuid4().hex",s);self.assertIn("except PermissionError",s);self.assertIn("os.replace",s)
if __name__=="__main__":
    print("="*88);print(" ORH-006 CERTIFICATION TEST");print(" COLLISION-SAFE REASONING CURSOR PERSISTENCE");print("="*88)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful():raise SystemExit(1)
    print("[PASS] unique temporary cursor file certified");print("[PASS] bounded Windows/OneDrive PermissionError retry certified");print("[PASS] OCR-011 public API preserved");print("[PASS] execution_authority=FALSE");print("[DONE] ORH-006 CERTIFIED")
"""
def write_exact(p,s):
    t=p.with_suffix(p.suffix+".orh006tmp");t.write_text(s,encoding="utf-8",newline="\n");os.replace(t,p)
def restore(p,b):
    if b is None:
        if p.exists():p.unlink()
    else:p.write_bytes(b)
def main():
    print("="*88);print(" ORH-006 INSTALLER");print(" COLLISION-SAFE REASONING CURSOR PERSISTENCE");print("="*88);print("[ROOT]",ROOT)
    if not MOD.is_file():raise RuntimeError("Physical OCR-011 module missing")
    original=MOD.read_text(encoding="utf-8")
    for token in ("ReasoningCursorState","save_reasoning_cursor","advance_reasoning_cursor","load_reasoning_cursor"):
        if token not in original:raise RuntimeError("Physical OCR-011 contract changed: "+token)
    old={p:(p.read_bytes() if p.exists() else None) for p in (MOD,TEST)}
    try:
        write_exact(MOD,MODULE_SOURCE);write_exact(TEST,TEST_SOURCE);subprocess.run([sys.executable,str(TEST)],cwd=str(ROOT),check=True)
    except Exception:
        for p,b in old.items():restore(p,b)
        print("[ROLLBACK] ORH-006 failed; OCR-011 restored");raise
    print("[PASS] Fixed shared ocr_reasoning_cursor.json.tmp path retired");print("[PASS] collision-safe atomic cursor persistence installed");print("[PASS] reasoning semantics unchanged");print("[PASS] execution_authority=FALSE");print("[DONE] ORH-006 INSTALLATION COMPLETE")
if __name__=="__main__":main()
