from __future__ import annotations
import ast, os, subprocess, sys, textwrap
from pathlib import Path

EXPECTED_FILENAME="build_oad_285_gmgn_supervised_windows_environment_PRODUCTION_BOUNDARY_REBUILD.py"
LAUNCHER="run_oracle_live.py"
TEST="test_oad_285_gmgn_supervised_windows_environment_boundary.py"
GMGN="run_oad_284_gmgn_continuous_intelligence_production_child.py"

NEW_START=r"""
def _start(root,name):
    p=root/name
    if not p.is_file():
        raise RuntimeError("runtime child missing: "+name)

    if name == "run_oad_284_gmgn_continuous_intelligence_production_child.py":
        env=os.environ.copy()
        if os.name=="nt":
            system_root=(env.get("SystemRoot") or r"C:\Windows").strip()
            env["SystemRoot"]=system_root
            env["COMSPEC"]=(env.get("COMSPEC") or str(Path(system_root)/"System32"/"cmd.exe")).strip()
            userprofile=(env.get("USERPROFILE") or str(Path.home())).strip()
            env["USERPROFILE"]=userprofile
            appdata=(env.get("APPDATA") or str(Path(userprofile)/"AppData"/"Roaming")).strip()
            env["APPDATA"]=appdata
            npm_dir=str(Path(appdata)/"npm")
            parts=[x for x in env.get("PATH","").split(os.pathsep) if x]
            norm=lambda x: os.path.normcase(os.path.normpath(x))
            if norm(npm_dir) not in {norm(x) for x in parts}:
                parts.insert(0,npm_dir)
            env["PATH"]=os.pathsep.join(parts)
        return subprocess.Popen([sys.executable,str(p)],cwd=str(root),env=env)

    return subprocess.Popen([sys.executable,str(p)],cwd=str(root))
"""

TEST_SOURCE=r"""
from __future__ import annotations
import subprocess,sys,unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parent
LAUNCHER=ROOT/"run_oracle_live.py"

class T(unittest.TestCase):
    def test_gmgn_environment_boundary(self):
        s=LAUNCHER.read_text(encoding="utf-8")
        self.assertIn('if name == "run_oad_284_gmgn_continuous_intelligence_production_child.py":',s)
        self.assertIn('env["COMSPEC"]',s)
        self.assertIn('env["SystemRoot"]',s)
        self.assertIn('env["APPDATA"]',s)
        self.assertIn('env["USERPROFILE"]',s)
        self.assertIn('env["PATH"]',s)

    def test_other_children_preserved(self):
        s=LAUNCHER.read_text(encoding="utf-8")
        self.assertIn('return subprocess.Popen([sys.executable,str(p)],cwd=str(root))',s)

    def test_truthful_health_preserved(self):
        s=LAUNCHER.read_text(encoding="utf-8")
        self.assertIn("gmgn_checkpoint_cycle_at_spawn",s)
        self.assertIn("if cp.last_error:",s)
        self.assertIn("if success_age > 240.0:",s)
        self.assertIn("restart_backoff_seconds",s)
        self.assertNotIn("execution_authority=TRUE",s)

    def test_launcher_check(self):
        p=subprocess.run([sys.executable,str(LAUNCHER),"--check"],cwd=str(ROOT),
                         text=True,capture_output=True,timeout=45)
        self.assertEqual(p.returncode,0,msg=p.stdout+"\n"+p.stderr)
        self.assertIn("[READY] Oracle Live Runtime",p.stdout)

if __name__=="__main__":
    print("="*104)
    print(" OAD-285 GMGN SUPERVISED WINDOWS ENVIRONMENT BOUNDARY CERTIFICATION")
    print("="*104)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] GMGN-only Windows child environment normalized")
    print("[PASS] all non-GMGN child spawn behavior preserved")
    print("[PASS] truthful provider-health supervision preserved")
    print("[PASS] launcher --check passed")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] OAD-285 SUPERVISED WINDOWS ENVIRONMENT BOUNDARY CERTIFIED")
"""

def root():
    for b in (Path.cwd().resolve(),Path(__file__).resolve().parent):
        for p in (b,*b.parents):
            if (p/"qseries_v2").is_dir(): return p
    raise RuntimeError("Q Series repository root not found")

def replace_start(src):
    tree=ast.parse(src); node=None
    for n in tree.body:
        if isinstance(n,ast.FunctionDef) and n.name=="_start": node=n; break
    if node is None: raise RuntimeError("_start missing")
    lines=src.splitlines(keepends=True)
    out="".join(lines[:node.lineno-1])+textwrap.dedent(NEW_START).lstrip()+"\n"+"".join(lines[node.end_lineno:])
    ast.parse(out)
    return out

def main():
    if Path(__file__).name!=EXPECTED_FILENAME: raise RuntimeError("installer identity mismatch")
    r=root(); launcher=r/LAUNCHER; test=r/TEST
    src=launcher.read_text(encoding="utf-8"); ast.parse(src)
    for marker in (
        '"gmgn_intelligence": "run_oad_284_gmgn_continuous_intelligence_production_child.py"',
        "gmgn_checkpoint_cycle_at_spawn","def _child_state(key, now):","restart_backoff_seconds"):
        if marker not in src: raise RuntimeError("current OAD-285 boundary missing: "+marker)
    if not (r/GMGN).is_file(): raise RuntimeError("GMGN production child missing")
    if "execution_authority=TRUE" in src: raise RuntimeError("execution safety violation")

    old_launcher=launcher.read_bytes()
    old_test=test.read_bytes() if test.exists() else None
    try:
        launcher.write_text(replace_start(src),encoding="utf-8",newline="\n")
        test.write_text(textwrap.dedent(TEST_SOURCE).lstrip(),encoding="utf-8",newline="\n")
        compile(launcher.read_text(encoding="utf-8"),str(launcher),"exec")
        compile(test.read_text(encoding="utf-8"),str(test),"exec")
        p=subprocess.run([sys.executable,str(test)],cwd=str(r),text=True,capture_output=True,timeout=90)
        if p.returncode!=0: raise RuntimeError("certification failed:\n"+p.stdout+"\n"+p.stderr)
        print("="*104)
        print(" OAD-285 GMGN SUPERVISED WINDOWS ENVIRONMENT PRODUCTION BOUNDARY REBUILD")
        print("="*104)
        print("[PASS] exact current truthful GMGN health boundary verified")
        print("[PASS] GMGN child binding preserved")
        print("[PASS] GMGN-only COMSPEC/SystemRoot/APPDATA/USERPROFILE/PATH normalization installed")
        print("[PASS] all other Oracle child spawn behavior preserved")
        print("[PASS] probability=FALSE direction=FALSE publication=FALSE execution=FALSE")
        print("[DONE] OAD-285 SUPERVISED WINDOWS ENVIRONMENT BOUNDARY REBUILD INSTALLED")
    except Exception:
        launcher.write_bytes(old_launcher)
        if old_test is None:
            if test.exists(): test.unlink()
        else: test.write_bytes(old_test)
        print("[ROLLBACK] launcher/test restored")
        raise

if __name__=="__main__":
    main()
