from pathlib import Path
import ast, importlib, os, subprocess, sys, time, hashlib

ROOT=Path.cwd().resolve()
MOD=ROOT/'qseries_v2/oracle_intelligence_analytics_runtime/oiar_008_oracle_live_analytics_child_binding.py'
TEST=ROOT/'test_oiar_008_oracle_live_analytics_child_binding.py'

MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass\n\nOIAR_008_BUILD_ID="OIAR-008"\nOIAR_008_REVISION="OIAR_008_ORACLE_LIVE_ANALYTICS_CHILD_BINDING_V1"\nCHILD_NAME="analytics"\nRUNNER="run_oiar_006_continuous_analytics_refresh_runtime.py"\n\n@dataclass(frozen=True)\nclass OracleLiveAnalyticsBinding:\n    child_name:str=CHILD_NAME\n    runner:str=RUNNER\n    supervised:bool=True\n    terminal_dependency:bool=False\n    execution_authority:bool=False\n\ndef verify_oiar_008_oracle_live_analytics_binding():\n    x=OracleLiveAnalyticsBinding()\n    return x.supervised and not x.terminal_dependency and not x.execution_authority\n'
TEST_SOURCE='import ast,unittest\nfrom pathlib import Path\nROOT=Path.cwd().resolve();L=ROOT/"run_oracle_LIVE.py"\ndef children():\n    tree=ast.parse(L.read_text(encoding="utf-8"))\n    for n in ast.walk(tree):\n        if isinstance(n,ast.Assign) and isinstance(n.value,ast.Dict) and any(isinstance(t,ast.Name) and t.id=="CHILDREN" for t in n.targets):\n            return {str(k.value):str(v.value) for k,v in zip(n.value.keys,n.value.values) if isinstance(k,ast.Constant) and isinstance(v,ast.Constant) and isinstance(v.value,str)}\n    raise AssertionError("CHILDREN missing")\nclass T(unittest.TestCase):\n    def test_binding(self):\n        c=children();self.assertEqual(c.get("analytics"),"run_oiar_006_continuous_analytics_refresh_runtime.py")\n    def test_proven_core_preserved(self):\n        c=children()\n        for k in ("fast_lane","inventory","reasoning","learning","coverage","canonical_writer","continuity","recovery"):\n            self.assertIn(k,c)\n    def test_nonblocking(self):\n        s=L.read_text(encoding="utf-8")\n        self.assertNotIn("run_refresh_cycle(",s)\n        self.assertNotIn("execution_authority=TRUE",s)\nif __name__=="__main__":\n    print("="*88);print(" OIAR-008 CERTIFICATION TEST");print(" ORACLE LIVE ANALYTICS CHILD BINDING");print("="*88)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful():raise SystemExit(1)\n    print("[PASS] analytics is independent supervised Oracle Live child")\n    print("[PASS] proven eight-child baseline preserved")\n    print("[PASS] no synchronous analytics call in launcher")\n    print("[PASS] execution_authority=FALSE")\n    print("[DONE] OIAR-008 CERTIFIED")\n'

def write_exact(path,text):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_name(path.name+f".{os.getpid()}.tmp")
    tmp.write_text(text,encoding="utf-8")
    os.replace(tmp,path)

def restore(path,data):
    if data is None:
        if path.exists(): path.unlink()
    else:
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_bytes(data)

def update_init(path,export):
    current=path.read_text(encoding="utf-8") if path.exists() else ""
    if export not in current.splitlines():
        write_exact(path,current.rstrip()+"\n"+export+"\n")

def main():
    print("="*88);print(" OIAR-008 INSTALLER");print(" ORACLE LIVE ANALYTICS CHILD BINDING");print("="*88);print("[ROOT]",ROOT)
    PKG=MOD.parent;INIT=PKG/"__init__.py";LAUNCHER=ROOT/"run_oracle_LIVE.py";RUNNER=ROOT/"run_oiar_006_continuous_analytics_refresh_runtime.py"
    if not LAUNCHER.is_file():raise RuntimeError("run_oracle_LIVE.py missing")
    if not RUNNER.is_file():raise RuntimeError("OIAR-006 runner missing")
    subprocess.run([sys.executable,str(RUNNER),"--check"],cwd=str(ROOT),check=True,timeout=10)

    def read_children(source):
        tree=ast.parse(source)
        for n in ast.walk(tree):
            if isinstance(n,ast.Assign) and isinstance(n.value,ast.Dict) and any(isinstance(t,ast.Name) and t.id=="CHILDREN" for t in n.targets):
                return {str(k.value):str(v.value) for k,v in zip(n.value.keys,n.value.values) if isinstance(k,ast.Constant) and isinstance(v,ast.Constant) and isinstance(v.value,str)}
        raise RuntimeError("Physical CHILDREN dictionary missing")

    def patch(source):
        ast.parse(source);before=read_children(source)
        required={"fast_lane","inventory","reasoning","learning","coverage","canonical_writer","continuity","recovery"}
        if not required.issubset(before):raise RuntimeError(f"Proven Oracle Live baseline changed: {sorted(required-set(before))}")
        if before.get("analytics")=="run_oiar_006_continuous_analytics_refresh_runtime.py":return source,before
        if "analytics" in before:raise RuntimeError("Existing analytics child points to unexpected runner")
        tree=ast.parse(source);assign=None
        for n in tree.body:
            if isinstance(n,ast.Assign) and isinstance(n.value,ast.Dict) and any(isinstance(t,ast.Name) and t.id=="CHILDREN" for t in n.targets):
                assign=n;break
        if assign is None:raise RuntimeError("CHILDREN assignment not patchable")
        lines=source.splitlines(keepends=True)
        if assign.lineno==assign.end_lineno:
            line=lines[assign.lineno-1];idx=line.rfind("}");prefix=line[:idx].rstrip();sep="" if prefix.endswith("{") else ","
            lines[assign.lineno-1]=prefix+sep+"'analytics':'run_oiar_006_continuous_analytics_refresh_runtime.py'"+line[idx:]
        else:
            indent=" "*(assign.col_offset+4)
            lines.insert(assign.end_lineno-1,indent+"'analytics':'run_oiar_006_continuous_analytics_refresh_runtime.py',\n")
        out="".join(lines);ast.parse(out);after=read_children(out)
        for k,v in before.items():
            if after.get(k)!=v:raise RuntimeError(f"Existing Oracle child changed: {k}")
        if after.get("analytics")!="run_oiar_006_continuous_analytics_refresh_runtime.py":raise RuntimeError("analytics insertion failed")
        return out,before

    old={p:(p.read_bytes() if p.exists() else None) for p in (MOD,TEST,INIT,LAUNCHER)}
    try:
        source=LAUNCHER.read_text(encoding="utf-8");patched,before=patch(source)
        write_exact(MOD,MODULE_SOURCE);write_exact(TEST,TEST_SOURCE);write_exact(LAUNCHER,patched)
        update_init(INIT,"from .oiar_008_oracle_live_analytics_child_binding import *")
        ast.parse(MODULE_SOURCE);ast.parse(TEST_SOURCE);ast.parse(patched)
        subprocess.run([sys.executable,str(TEST)],cwd=str(ROOT),check=True)
        subprocess.run([sys.executable,str(LAUNCHER),"--check"],cwd=str(ROOT),check=True,timeout=30)
    except Exception:
        for p,b in old.items():restore(p,b)
        print("[ROLLBACK] OIAR-008 failed; launcher and affected files restored");raise
    print("[PASS] existing Oracle Live children preserved exactly")
    print("[PASS] analytics added only as independent child")
    print("[PASS] Oracle Live startup remains non-blocking")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] OIAR-008 INSTALLATION COMPLETE")

if __name__=="__main__":
    main()
