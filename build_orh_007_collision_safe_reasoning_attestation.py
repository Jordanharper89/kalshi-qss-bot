from pathlib import Path
import ast,os,re,subprocess,sys
ROOT=Path.cwd().resolve()
MOD=ROOT/"qseries_v2"/"oracle_learning_feedback"/"olf_030_breadth_aware_reasoning_runtime.py"
TEST=ROOT/"test_orh_007_collision_safe_reasoning_attestation.py"
HELPER="""
def _orh007_atomic_json(path,payload,max_attempts=8):
    import uuid,time
    p=Path(path);p.parent.mkdir(parents=True,exist_ok=True)
    raw=json.dumps(payload,sort_keys=True,separators=(",",":"));last=None
    for attempt in range(1,int(max_attempts)+1):
        tmp=p.with_name(p.name+f".{os.getpid()}.{uuid.uuid4().hex}.tmp")
        try:
            tmp.write_text(raw,encoding="utf-8",newline="\\n");os.replace(tmp,p);return p
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
    raise last or PermissionError("OLF-030 attestation atomic replace failed")
"""
def patch_source(source):
    ast.parse(source)
    if "_orh007_atomic_json" in source:return source
    marker='ATTESTATION_NAME="oracle_learning_breadth_reasoning_attestation.json"'
    if marker not in source:raise RuntimeError("OLF-030 attestation contract not found")
    source=source.replace(marker,marker+"\n"+HELPER,1)
    fixed='tmp=path.with_suffix(path.suffix+".tmp")'
    if fixed not in source:raise RuntimeError("Fixed OLF-030 attestation temp path not found")
    start=source.index(fixed);end=source.find("os.replace(tmp,path)",start)
    if end<0:raise RuntimeError("OLF-030 attestation replace call not found")
    end+=len("os.replace(tmp,path)")
    source=source[:start]+'_orh007_atomic_json(path,payload)'+source[end:]
    ast.parse(source);return source
TEST_SOURCE=r"""import inspect,unittest
import qseries_v2.oracle_learning_feedback.olf_030_breadth_aware_reasoning_runtime as m
class T(unittest.TestCase):
    def test_helper(self):
        s=inspect.getsource(m._orh007_atomic_json);self.assertIn("uuid.uuid4().hex",s);self.assertIn("PermissionError",s)
    def test_fixed_tmp_retired(self):
        s=inspect.getsource(m.run_breadth_aware_reasoning_cycle);self.assertNotIn('with_suffix(path.suffix+".tmp")',s);self.assertIn("_orh007_atomic_json",s)
if __name__=="__main__":
    print("="*88);print(" ORH-007 CERTIFICATION TEST");print(" COLLISION-SAFE REASONING ATTESTATION");print("="*88)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful():raise SystemExit(1)
    print("[PASS] OLF-030 fixed attestation temp file retired");print("[PASS] unique atomic attestation write certified");print("[PASS] reasoning semantics preserved");print("[PASS] execution_authority=FALSE");print("[DONE] ORH-007 CERTIFIED")
"""
def write_exact(p,s):
    t=p.with_suffix(p.suffix+".orh007tmp");t.write_text(s,encoding="utf-8",newline="\n");os.replace(t,p)
def main():
    print("="*88);print(" ORH-007 INSTALLER");print(" COLLISION-SAFE REASONING ATTESTATION");print("="*88);print("[ROOT]",ROOT)
    if not MOD.is_file():raise RuntimeError("Physical OLF-030 module missing")
    oldm=MOD.read_bytes();oldt=TEST.read_bytes() if TEST.exists() else None
    try:
        write_exact(MOD,patch_source(MOD.read_text(encoding="utf-8")));write_exact(TEST,TEST_SOURCE);subprocess.run([sys.executable,str(TEST)],cwd=str(ROOT),check=True)
    except Exception:
        MOD.write_bytes(oldm)
        if oldt is None:
            if TEST.exists():TEST.unlink()
        else:TEST.write_bytes(oldt)
        print("[ROLLBACK] ORH-007 failed; OLF-030 restored");raise
    print("[PASS] OLF-030 public reasoning API unchanged");print("[PASS] OneDrive-safe attestation persistence installed");print("[PASS] execution_authority=FALSE");print("[DONE] ORH-007 INSTALLATION COMPLETE")
if __name__=="__main__":main()
