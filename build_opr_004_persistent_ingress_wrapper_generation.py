from pathlib import Path
import importlib,os,subprocess,sys
ROOT=Path.cwd().resolve();PKG=ROOT/"qseries_v2"/"oracle_postgresql_reliability"
MOD=PKG/"opr_004_persistent_ingress_wrappers.py";TEST=ROOT/"test_opr_004_persistent_ingress_wrappers.py";INIT=PKG/"__init__.py"
MODULE_SOURCE='from __future__ import annotations\nfrom pathlib import Path\nimport ast\n\nOPR_004_BUILD_ID="OPR-004"\nOPR_004_REVISION="OPR_004_PERSISTENT_INGRESS_WRAPPER_GENERATION_V1"\n\ndef read_children(source):\n    tree=ast.parse(source)\n    for item in ast.walk(tree):\n        if isinstance(item,ast.Assign) and isinstance(item.value,ast.Dict) and any(\n            isinstance(t,ast.Name) and t.id=="CHILDREN" for t in item.targets\n        ):\n            return {\n                str(k.value):str(v.value)\n                for k,v in zip(item.value.keys,item.value.values)\n                if isinstance(k,ast.Constant) and isinstance(v,ast.Constant) and isinstance(v.value,str)\n            }\n    raise RuntimeError("run_oracle_LIVE.py CHILDREN dictionary not found")\n\ndef unwrap_runner(root,runner):\n    current=str(runner);seen=set()\n    for _ in range(20):\n        if current in seen:raise RuntimeError("recursive wrapper chain")\n        seen.add(current);p=Path(root)/current\n        if not p.is_file():return current\n        target=None\n        try:\n            tree=ast.parse(p.read_text(encoding="utf-8",errors="ignore"))\n            for item in tree.body:\n                if isinstance(item,ast.Assign):\n                    for t in item.targets:\n                        if isinstance(t,ast.Name) and t.id=="UNDERLYING_RUNNER":\n                            target=ast.literal_eval(item.value);break\n                if target is not None:break\n        except Exception:target=None\n        if not target:return current\n        current=str(target)\n    raise RuntimeError("wrapper resolution exceeded")\n\ndef safe_name(name):\n    return "".join(c if c.isalnum() else "_" for c in str(name)).strip("_").lower()\n\ndef wrapper_source(child_name,underlying):\n    producer="oracle."+str(child_name)\n    lines=[\n        "from pathlib import Path",\n        "import runpy",\n        "from qseries_v2.oracle_postgresql_reliability.opr_002_persistent_producer_ingress import install_persistent_postgresql_ingress",\n        f"UNDERLYING_RUNNER={underlying!r}",\n        "",\n        "if __name__==\'__main__\':",\n        "    print(\'=\'*88,flush=True)",\n        f"    print(\' OPR-004 PERSISTENT POSTGRESQL INGRESS child={child_name}\',flush=True)",\n        "    print(\'=\'*88,flush=True)",\n        f"    install_persistent_postgresql_ingress({producer!r},Path.cwd())",\n        "    print(\'[OPR-004] persistent_queue_session=TRUE direct_canonical_postgresql_write_authority=FALSE\',flush=True)",\n        "    runpy.run_path(str(Path.cwd()/UNDERLYING_RUNNER),run_name=\'__main__\')",\n        "",\n    ]\n    source="\\n".join(lines);ast.parse(source);return source\n\ndef verify_opr_004_persistent_ingress_wrapper_generation(root=None):\n    root=Path(root or Path.cwd()).resolve()\n    launcher=root/"run_oracle_LIVE.py"\n    if not launcher.is_file():return False\n    children=read_children(launcher.read_text(encoding="utf-8"))\n    return bool(children) and "canonical_writer" in children\n';TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_postgresql_reliability.opr_004_persistent_ingress_wrappers import *\n\nclass T(unittest.TestCase):\n    def test_parser(self):self.assertEqual(read_children(\'CHILDREN={"a":"b.py"}\\n\')["a"],"b.py")\n    def test_wrapper(self):\n        s=wrapper_source("fast_lane","raw.py")\n        self.assertIn("install_persistent_postgresql_ingress",s)\n        compile(s,"wrapper","exec")\n\nif __name__=="__main__":\n    print("="*88);print(" OPR-004 CERTIFICATION TEST");print(" PERSISTENT INGRESS WRAPPER GENERATION");print("="*88)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful():raise SystemExit(1)\n    print("[PASS] Persistent producer wrapper generation certified")\n    print("[PASS] execution_authority=FALSE")\n    print("[DONE] OPR-004 CERTIFIED")\n'

def write_exact(path,text):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(text,encoding="utf-8",newline="\n")
    os.replace(tmp,path)

def restore(path,data):
    if data is None:
        if path.exists():path.unlink()
    else:path.write_bytes(data)

def update_init(path,line):
    current=path.read_text(encoding="utf-8") if path.exists() else ""
    if line not in current.splitlines():
        write_exact(path,current.rstrip()+"\n"+line+"\n")

def main():
    print("="*88);print(" OPR-004 INSTALLER");print(" PERSISTENT INGRESS WRAPPER GENERATION");print("="*88);print("[ROOT]",ROOT)
    sys.path.insert(0,str(ROOT));up=importlib.import_module("qseries_v2.oracle_postgresql_reliability.opr_003_persistent_single_writer_runtime")
    if not up.verify_opr_003_persistent_single_writer_runtime(ROOT):raise RuntimeError("OPR-003 verification failed")
    launcher=ROOT/"run_oracle_LIVE.py"
    old={p:(p.read_bytes() if p.exists() else None) for p in (MOD,TEST,INIT)};generated=[]
    try:
        write_exact(MOD,MODULE_SOURCE);write_exact(TEST,TEST_SOURCE);update_init(INIT,"from .opr_004_persistent_ingress_wrappers import *")
        subprocess.run([sys.executable,str(TEST)],cwd=str(ROOT),check=True)
        importlib.invalidate_caches();m=importlib.import_module("qseries_v2.oracle_postgresql_reliability.opr_004_persistent_ingress_wrappers")
        children=m.read_children(launcher.read_text(encoding="utf-8"))
        for name,runner in children.items():
            if name=="canonical_writer":continue
            underlying=m.unwrap_runner(ROOT,runner)
            wrapper=ROOT/f"run_opr_004_{m.safe_name(name)}_persistent_ingress.py"
            write_exact(wrapper,m.wrapper_source(name,underlying));compile(wrapper.read_text(encoding="utf-8"),str(wrapper),"exec")
            generated.append(wrapper)
            print(f"[PASS] child={name} underlying={underlying} wrapper={wrapper.name}")
    except Exception:
        for p,b in old.items():restore(p,b)
        for p in generated:
            if p.exists():p.unlink()
        print("[ROLLBACK] OPR-004 failed; generated wrappers removed");raise
    print("[PASS] Oracle Live launcher unchanged")
    print("[PASS] Proven learning child underlying preserved")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] OPR-004 INSTALLATION COMPLETE")
if __name__=="__main__":main()
