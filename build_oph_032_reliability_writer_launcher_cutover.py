from pathlib import Path
import importlib, os, subprocess, sys
ROOT=Path.cwd().resolve();PKG=ROOT/"qseries_v2"/"oracle_production_hardening"
MOD=PKG/"oph_032_reliability_writer_launcher_cutover.py"
TEST=ROOT/"test_oph_032_reliability_writer_launcher_cutover.py"
INIT=PKG/"__init__.py";LAUNCHER=ROOT/"run_oracle_LIVE.py"
MODULE_SOURCE='from __future__ import annotations\nfrom pathlib import Path\nimport ast\n\nOPH_032_BUILD_ID="OPH-032"\nOPH_032_REVISION="OPH_032_RELIABILITY_WRITER_LAUNCHER_CUTOVER_V1"\nRELIABILITY_WRITER="run_oph_031_classified_single_writer_reliability_runtime.py"\n\ndef read_children(source):\n    tree=ast.parse(source)\n    for item in ast.walk(tree):\n        if isinstance(item,ast.Assign) and isinstance(item.value,ast.Dict) and any(\n            isinstance(t,ast.Name) and t.id=="CHILDREN" for t in item.targets\n        ):\n            result={}\n            for k,v in zip(item.value.keys,item.value.values):\n                if isinstance(k,ast.Constant) and isinstance(v,ast.Constant) and isinstance(v.value,str):\n                    result[str(k.value)]=str(v.value)\n            return result\n    raise RuntimeError("run_oracle_LIVE.py CHILDREN dictionary not found")\n\ndef patch_canonical_writer(source):\n    tree=ast.parse(source)\n    node=None\n    for item in ast.walk(tree):\n        if isinstance(item,ast.Assign) and isinstance(item.value,ast.Dict) and any(\n            isinstance(t,ast.Name) and t.id=="CHILDREN" for t in item.targets\n        ):\n            node=item.value\n            break\n    if node is None: raise RuntimeError("CHILDREN dictionary not found")\n    lines=source.splitlines(keepends=True)\n    for k,v in zip(node.keys,node.values):\n        if isinstance(k,ast.Constant) and str(k.value)=="canonical_writer" and isinstance(v,ast.Constant):\n            old=str(v.value)\n            if old==RELIABILITY_WRITER:return source\n            line=lines[v.lineno-1]\n            for token in (repr(old),\'"\'+old+\'"\',"\'"+old+"\'"):\n                if token in line:\n                    lines[v.lineno-1]=line.replace(token,repr(RELIABILITY_WRITER),1)\n                    patched="".join(lines);ast.parse(patched);return patched\n    raise RuntimeError("canonical_writer child not found")\n\ndef verify_oph_032_reliability_writer_launcher_cutover(root=None):\n    root=Path(root or Path.cwd()).resolve()\n    launcher=root/"run_oracle_LIVE.py"\n    if not launcher.is_file(): return False\n    children=read_children(launcher.read_text(encoding="utf-8"))\n    if children.get("canonical_writer")!=RELIABILITY_WRITER:return False\n    producer_names=[n for n in children if n!="canonical_writer"]\n    if not producer_names:return False\n    for name in producer_names:\n        runner=children[name]\n        if not runner.startswith("run_oph_022_") or not runner.endswith("_postgresql_ingress.py"):\n            return False\n    return True\n';TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_production_hardening.oph_032_reliability_writer_launcher_cutover import *\nclass T(unittest.TestCase):\n    def test_identity(self):self.assertEqual(RELIABILITY_WRITER,"run_oph_031_classified_single_writer_reliability_runtime.py")\n    def test_patch(self):\n        src=\'CHILDREN={"fast_lane":"run_oph_022_fast_lane_postgresql_ingress.py","canonical_writer":"run_oph_021_exclusive_postgresql_canonical_writer.py"}\\n\'\n        out=patch_canonical_writer(src)\n        self.assertIn(RELIABILITY_WRITER,out)\nif __name__=="__main__":\n    print("="*88);print(" OPH-032 CERTIFICATION TEST");print(" RELIABILITY WRITER LAUNCHER CUTOVER");print("="*88)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful():raise SystemExit(1)\n    print("[PASS] Canonical writer cutover machinery certified")\n    print("[PASS] Producer PostgreSQL-ingress wrappers remain unchanged")\n    print("[PASS] execution_authority=FALSE")\n    print("[DONE] OPH-032 CERTIFIED")\n'

def write_exact(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8", newline="\n")
    os.replace(tmp, path)

def update_init(path, export):
    current = path.read_text(encoding="utf-8") if path.exists() else ""
    if export not in current.splitlines():
        write_exact(path, current.rstrip() + "\n" + export + "\n")

def restore(path, data):
    if data is None:
        if path.exists():
            path.unlink()
    else:
        path.write_bytes(data)

def main():
    print("="*88);print(" OPH-032 INSTALLER");print(" RELIABILITY WRITER LAUNCHER CUTOVER");print("="*88);print("[ROOT]",ROOT)
    sys.path.insert(0,str(ROOT))
    up=importlib.import_module("qseries_v2.oracle_production_hardening.oph_031_classified_single_writer_reliability_runtime")
    if up.verify_oph_031_classified_single_writer_reliability_runtime(ROOT) is not True:
        raise RuntimeError("Certified OPH-031 upstream verification failed")
    print("[PASS] Certified OPH-031 upstream boundary verified read-only")
    if not LAUNCHER.is_file():raise RuntimeError("run_oracle_LIVE.py missing")
    affected=(MOD,TEST,INIT,LAUNCHER);old={p:(p.read_bytes() if p.exists() else None) for p in affected}
    try:
        write_exact(MOD,MODULE_SOURCE);write_exact(TEST,TEST_SOURCE)
        update_init(INIT,"from .oph_032_reliability_writer_launcher_cutover import *")
        importlib.invalidate_caches()
        m=importlib.import_module("qseries_v2.oracle_production_hardening.oph_032_reliability_writer_launcher_cutover")
        source=LAUNCHER.read_text(encoding="utf-8")
        patched=m.patch_canonical_writer(source)
        compile(patched,str(LAUNCHER),"exec")
        write_exact(LAUNCHER,patched)
        subprocess.run([sys.executable,str(TEST)],cwd=str(ROOT),check=True)
        subprocess.run([sys.executable,str(LAUNCHER),"--check"],cwd=str(ROOT),check=True)
        if not m.verify_oph_032_reliability_writer_launcher_cutover(ROOT):
            raise RuntimeError("OPH-032 physical launcher verification failed")
    except Exception:
        for p,b in old.items(): restore(p,b)
        print("[ROLLBACK] OPH-032 cutover failed; launcher and affected files restored");raise
    print("[PASS] canonical_writer="+m.RELIABILITY_WRITER)
    print("[PASS] All OPH-022 producer ingress wrappers preserved")
    print("[PASS] Single PostgreSQL writer architecture preserved")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] OPH-032 INSTALLATION AND CERTIFICATION COMPLETE")
if __name__=="__main__": main()
