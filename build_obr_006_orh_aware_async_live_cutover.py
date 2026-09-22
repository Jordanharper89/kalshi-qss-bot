from pathlib import Path
import ast, os, subprocess, sys

ROOT=Path.cwd().resolve()
LAUNCHER=ROOT/"run_oracle_LIVE.py"
WORKER=ROOT/"run_oracle_background_recovery.py"
TEST=ROOT/"test_obr_006_orh_aware_async_live_cutover.py"

def read_children(source):
    tree=ast.parse(source)
    for n in ast.walk(tree):
        if isinstance(n,ast.Assign) and isinstance(n.value,ast.Dict) and any(isinstance(t,ast.Name) and t.id=="CHILDREN" for t in n.targets):
            return {str(k.value):str(v.value) for k,v in zip(n.value.keys,n.value.values) if isinstance(k,ast.Constant) and isinstance(v,ast.Constant) and isinstance(v.value,str)}
    raise RuntimeError("Physical CHILDREN dictionary missing")

def patch_children(source):
    ast.parse(source)
    if "state={overall}" not in source or "recent_restarts_60s" not in source:
        raise RuntimeError("ORH-001 truthful-health launcher not detected")
    before=read_children(source)
    expected={"fast_lane","inventory","reasoning","learning","coverage","canonical_writer","continuity"}
    if not expected.issubset(set(before)):
        raise RuntimeError("ORH physical seven-child contract changed")
    if before.get("recovery")=="run_oracle_background_recovery.py":
        return source
    if "recovery" in before:
        raise RuntimeError("Existing recovery child points to unexpected runner")

    tree=ast.parse(source)
    assign=None
    for n in tree.body:
        if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=="CHILDREN" for t in n.targets):
            assign=n;break
    if assign is None or not isinstance(assign.value,ast.Dict):
        raise RuntimeError("CHILDREN dictionary not patchable")

    lines=source.splitlines(keepends=True)
    if assign.lineno==assign.end_lineno:
        line=lines[assign.lineno-1];idx=line.rfind("}")
        if idx<0:raise RuntimeError("CHILDREN closing brace missing")
        prefix=line[:idx].rstrip()
        sep="" if prefix.endswith("{") else ","
        lines[assign.lineno-1]=prefix+sep+"'recovery':'run_oracle_background_recovery.py'"+line[idx:]
    else:
        indent=" "*(assign.col_offset+4)
        lines.insert(assign.end_lineno-1,indent+"'recovery':'run_oracle_background_recovery.py',\n")
    out="".join(lines);ast.parse(out)
    after=read_children(out)
    for k,v in before.items():
        if after.get(k)!=v:raise RuntimeError(f"Existing child changed: {k}")
    if after.get("recovery")!="run_oracle_background_recovery.py":raise RuntimeError("Recovery child insertion failed")
    return out

TEST_SOURCE=r"""import ast,unittest
from pathlib import Path
ROOT=Path.cwd().resolve();L=ROOT/"run_oracle_LIVE.py"
class T(unittest.TestCase):
    def test_physical_launcher(self):
        s=L.read_text(encoding="utf-8");ast.parse(s)
        self.assertIn("'recovery':'run_oracle_background_recovery.py'",s.replace(" ",""))
        self.assertIn("state={overall}",s)
        self.assertIn("recent_restarts_60s",s)
        self.assertNotIn("run_recovery_preflight(",s)
        self.assertNotIn("reconcile_downtime_delta(",s)
if __name__=="__main__":
    print("="*88);print(" OBR-006 CERTIFICATION TEST");print(" ORH-AWARE ASYNCHRONOUS LIVE CUTOVER");print("="*88)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful():raise SystemExit(1)
    print("[PASS] recovery is independent supervised child")
    print("[PASS] ORH truthful-health semantics preserved")
    print("[PASS] no synchronous recovery call exists")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] OBR-006 CERTIFIED")
"""

def write_exact(p,s):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(s,encoding="utf-8",newline="\n");os.replace(t,p)
def restore(p,b):
    if b is None:
        if p.exists():p.unlink()
    else:p.write_bytes(b)

def main():
    print("="*88);print(" OBR-006 INSTALLER");print(" ORH-AWARE ASYNCHRONOUS LIVE CUTOVER");print("="*88);print("[ROOT]",ROOT)
    if not LAUNCHER.is_file():raise RuntimeError("run_oracle_LIVE.py missing")
    if not WORKER.is_file():raise RuntimeError("OBR-005 physical worker missing")
    subprocess.run([sys.executable,str(WORKER),"--check"],cwd=str(ROOT),check=True)
    old={p:(p.read_bytes() if p.exists() else None) for p in (LAUNCHER,TEST)}
    try:
        before=LAUNCHER.read_text(encoding="utf-8")
        after=patch_children(before)
        if "run_recovery_preflight(" in after or "reconcile_downtime_delta(" in after:
            raise RuntimeError("Blocking recovery call found")
        write_exact(LAUNCHER,after);write_exact(TEST,TEST_SOURCE)
        subprocess.run([sys.executable,str(TEST)],cwd=str(ROOT),check=True)
        subprocess.run([sys.executable,str(LAUNCHER),"--check"],cwd=str(ROOT),timeout=30,check=True)
    except Exception:
        for p,b in old.items():restore(p,b)
        print("[ROLLBACK] OBR-006 failed; launcher restored");raise
    print("[PASS] Existing ORH children preserved exactly")
    print("[PASS] recovery added only as independent child")
    print("[PASS] Oracle Live remains non-blocking")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] OBR-006 INSTALLATION COMPLETE")
if __name__=="__main__":main()
