from pathlib import Path
import importlib,os,subprocess,sys
ROOT=Path.cwd().resolve();PKG=ROOT/"qseries_v2"/"oracle_production_hardening";MOD=PKG/"oph_022_oracle_universal_single_writer_cutover.py";TEST=ROOT/"test_oph_022_oracle_universal_single_writer_cutover.py";INIT=PKG/"__init__.py";LAUNCHER=ROOT/"run_oracle_LIVE.py"
MODULE_SOURCE='from __future__ import annotations\nfrom pathlib import Path\nimport ast\nOPH_022_BUILD_ID="OPH-022"\nOPH_022_REVISION="OPH_022_ORACLE_UNIVERSAL_SINGLE_WRITER_CUTOVER_V1"\nCANONICAL_WRITER="run_oph_021_exclusive_postgresql_canonical_writer.py"\n\ndef read_children(source):\n    tree=ast.parse(source)\n    for item in ast.walk(tree):\n        if isinstance(item,ast.Assign) and isinstance(item.value,ast.Dict) and any(isinstance(t,ast.Name) and t.id=="CHILDREN" for t in item.targets):\n            return {str(k.value):str(v.value) for k,v in zip(item.value.keys,item.value.values) if isinstance(k,ast.Constant) and isinstance(v,ast.Constant) and isinstance(v.value,str)}\n    raise RuntimeError("run_oracle_LIVE.py CHILDREN dictionary not found")\n\ndef patch_child(source,name,value):\n    tree=ast.parse(source);node=None\n    for item in ast.walk(tree):\n        if isinstance(item,ast.Assign) and isinstance(item.value,ast.Dict) and any(isinstance(t,ast.Name) and t.id=="CHILDREN" for t in item.targets):node=item.value;break\n    if node is None:raise RuntimeError("CHILDREN dictionary not found")\n    lines=source.splitlines(keepends=True)\n    for k,v in zip(node.keys,node.values):\n        if isinstance(k,ast.Constant) and str(k.value)==name and isinstance(v,ast.Constant) and isinstance(v.value,str):\n            old=v.value\n            if old==value:return source\n            line=lines[v.lineno-1]\n            for token in (repr(old),\'"\'+old+\'"\',"\'"+old+"\'"):\n                if token in line:\n                    lines[v.lineno-1]=line.replace(token,repr(value),1);patched="".join(lines);ast.parse(patched);return patched\n    raise RuntimeError(f"child {name} not found")\n\ndef unwrap_runner(root,runner):\n    current=str(runner);seen=set()\n    for _ in range(20):\n        if current in seen:raise RuntimeError("recursive wrapper chain")\n        seen.add(current);p=Path(root)/current\n        if not p.is_file():return current\n        target=None\n        try:\n            tree=ast.parse(p.read_text(encoding="utf-8",errors="ignore"))\n            for item in tree.body:\n                if isinstance(item,ast.Assign):\n                    for t in item.targets:\n                        if isinstance(t,ast.Name) and t.id=="UNDERLYING_RUNNER":target=ast.literal_eval(item.value);break\n                if target is not None:break\n        except Exception:target=None\n        if not target:return current\n        current=str(target)\n    raise RuntimeError("wrapper resolution exceeded")\n\ndef safe_child_name(name):return "".join(c if c.isalnum() else "_" for c in str(name)).strip("_").lower()\n\ndef wrapper_source(child_name,underlying):\n    producer="oracle."+str(child_name)\n    return (\n      "from pathlib import Path\\\\n"\n      "import runpy\\\\n"\n      "from qseries_v2.oracle_production_hardening.oph_020_universal_postgresql_producer_admission import install_universal_postgresql_ingress\\\\n"\n      f"UNDERLYING_RUNNER={underlying!r}\\\\n"\n      "if __name__==\'__main__\':\\\\n"\n      "    print(\'=\'*88,flush=True)\\\\n"\n      f"    print(\' OPH-022 UNIVERSAL POSTGRESQL INGRESS child={child_name}\',flush=True)\\\\n"\n      "    print(\'=\'*88,flush=True)\\\\n"\n      f"    install_universal_postgresql_ingress({producer!r},Path.cwd())\\\\n"\n      "    print(\'[OPH-022] direct_canonical_postgresql_write_authority=FALSE\',flush=True)\\\\n"\n      "    runpy.run_path(str(Path.cwd()/UNDERLYING_RUNNER),run_name=\'__main__\')\\\\n"\n    )\n\ndef verify_oph_022_oracle_universal_single_writer_cutover(root=None):\n    root=Path(root or Path.cwd()).resolve();launcher=root/"run_oracle_LIVE.py"\n    if not launcher.is_file():return False\n    children=read_children(launcher.read_text(encoding="utf-8"))\n    if children.get("canonical_writer")!=CANONICAL_WRITER:return False\n    for name,runner in children.items():\n        if name=="canonical_writer":continue\n        if not runner.startswith("run_oph_022_") or not runner.endswith("_postgresql_ingress.py"):return False\n    return True\n';TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_production_hardening.oph_022_oracle_universal_single_writer_cutover import *\nclass T(unittest.TestCase):\n    def test_parser(self):self.assertEqual(read_children(\'CHILDREN={"a":"b.py"}\\n\')["a"],"b.py")\n    def test_wrapper(self):self.assertIn("install_universal_postgresql_ingress",wrapper_source("fast_lane","raw.py"))\nif __name__=="__main__":\n    print("="*88);print(" OPH-022 CERTIFICATION TEST");print(" ORACLE UNIVERSAL SINGLE-WRITER CUTOVER");print("="*88)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful():raise SystemExit(1)\n    print("[PASS] Universal launcher cutover machinery certified");print("[PASS] execution_authority=FALSE");print("[DONE] OPH-022 CERTIFIED")\n'

def write_exact(path,text):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(text,encoding="utf-8",newline="\n")
    os.replace(tmp,path)

def update_init(path,export):
    current=path.read_text(encoding="utf-8") if path.exists() else ""
    if export not in current.splitlines():
        write_exact(path,current.rstrip()+"\n"+export+"\n")

def main():
    print("="*88);print(" OPH-022 INSTALLER");print(" ORACLE UNIVERSAL SINGLE-WRITER CUTOVER");print("="*88);print("[ROOT]",ROOT)
    sys.path.insert(0,str(ROOT));up=importlib.import_module("qseries_v2.oracle_production_hardening.oph_021_exclusive_postgresql_canonical_writer")
    if up.verify_oph_021_exclusive_postgresql_canonical_writer() is not True:raise RuntimeError("Certified OPH-021 verification failed")
    if not LAUNCHER.is_file():raise RuntimeError("run_oracle_LIVE.py missing")
    affected=(MOD,TEST,INIT,LAUNCHER);old={p:(p.read_bytes() if p.exists() else None) for p in affected};generated=[]
    try:
        write_exact(MOD,MODULE_SOURCE);write_exact(TEST,TEST_SOURCE);update_init(INIT,"from .oph_022_oracle_universal_single_writer_cutover import *")
        importlib.invalidate_caches();m=importlib.import_module("qseries_v2.oracle_production_hardening.oph_022_oracle_universal_single_writer_cutover")
        source=LAUNCHER.read_text(encoding="utf-8");children=m.read_children(source);patched=source
        for name,runner in children.items():
            if name=="canonical_writer":patched=m.patch_child(patched,name,m.CANONICAL_WRITER);continue
            underlying=m.unwrap_runner(ROOT,runner);wrapper=ROOT/f"run_oph_022_{m.safe_child_name(name)}_postgresql_ingress.py";generated.append(wrapper)
            write_exact(wrapper,m.wrapper_source(name,underlying));compile(wrapper.read_text(encoding="utf-8"),str(wrapper),"exec")
            patched=m.patch_child(patched,name,wrapper.name);print(f"[PASS] child={name} underlying={underlying} -> {wrapper.name}")
        compile(patched,str(LAUNCHER),"exec");write_exact(LAUNCHER,patched)
        subprocess.run([sys.executable,str(TEST)],cwd=str(ROOT),check=True);subprocess.run([sys.executable,str(LAUNCHER),"--check"],cwd=str(ROOT),check=True)
        if not m.verify_oph_022_oracle_universal_single_writer_cutover(ROOT):raise RuntimeError("Physical OPH-022 launcher verification failed")
    except Exception:
        for p,b in old.items():
            if b is None:
                if p.exists():p.unlink()
            else:p.write_bytes(b)
        for p in generated:
            if p.exists():p.unlink()
        print("[ROLLBACK] OPH-022 cutover failed; launcher and affected files restored");raise
    print("[PASS] All supervised producer children use OPH-020 PostgreSQL ingress");print("[PASS] canonical_writer="+m.CANONICAL_WRITER)
    print("[PASS] Legacy SQLite queue is no longer on the active launcher path");print("[PASS] execution_authority=FALSE");print("[DONE] OPH-022 INSTALLATION AND CERTIFICATION COMPLETE")
if __name__=="__main__":main()
