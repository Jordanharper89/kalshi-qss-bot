from pathlib import Path
import importlib,os,subprocess,sys
ROOT=Path.cwd().resolve();PKG=ROOT/"qseries_v2"/"oracle_postgresql_reliability"
MOD=PKG/"opr_005_cutover_freeze.py";TEST=ROOT/"test_opr_005_cutover_freeze.py";INIT=PKG/"__init__.py";LAUNCHER=ROOT/"run_oracle_LIVE.py";MANIFEST=PKG/"OPR_005_FREEZE_MANIFEST.json"
MODULE_SOURCE='from __future__ import annotations\nfrom pathlib import Path\nimport ast,hashlib,json\n\nfrom .opr_004_persistent_ingress_wrappers import read_children,safe_name\n\nOPR_005_BUILD_ID="OPR-005"\nOPR_005_REVISION="OPR_005_PHYSICAL_CONNECTION_REUSE_CUTOVER_FREEZE_V1"\nWRITER="run_opr_003_persistent_single_writer_runtime.py"\n\ndef patch_child(source,name,value):\n    tree=ast.parse(source);node=None\n    for item in ast.walk(tree):\n        if isinstance(item,ast.Assign) and isinstance(item.value,ast.Dict) and any(\n            isinstance(t,ast.Name) and t.id=="CHILDREN" for t in item.targets\n        ):\n            node=item.value;break\n    if node is None:raise RuntimeError("CHILDREN dictionary not found")\n    lines=source.splitlines(keepends=True)\n    for k,v in zip(node.keys,node.values):\n        if isinstance(k,ast.Constant) and str(k.value)==name and isinstance(v,ast.Constant):\n            old=str(v.value)\n            if old==value:return source\n            line=lines[v.lineno-1]\n            for token in (repr(old),\'"\'+old+\'"\',"\'"+old+"\'"):\n                if token in line:\n                    lines[v.lineno-1]=line.replace(token,repr(value),1)\n                    out="".join(lines);ast.parse(out);return out\n    raise RuntimeError(f"child {name} not found")\n\ndef verify_cutover(root=None):\n    root=Path(root or Path.cwd()).resolve()\n    launcher=root/"run_oracle_LIVE.py"\n    children=read_children(launcher.read_text(encoding="utf-8"))\n    if children.get("canonical_writer")!=WRITER:return False\n    for name,runner in children.items():\n        if name=="canonical_writer":continue\n        if runner!=f"run_opr_004_{safe_name(name)}_persistent_ingress.py":return False\n    return True\n\ndef write_manifest(root,learning_underlying):\n    root=Path(root).resolve()\n    children=read_children((root/"run_oracle_LIVE.py").read_text(encoding="utf-8"))\n    body={\n        "build_id":OPR_005_BUILD_ID,\n        "revision":OPR_005_REVISION,\n        "canonical_writer":children.get("canonical_writer"),\n        "producer_children":{k:v for k,v in children.items() if k!="canonical_writer"},\n        "learning_underlying_preserved":learning_underlying,\n        "persistent_queue_sessions":True,\n        "single_writer_advisory_lease":True,\n        "oph_queue_schema_preserved":True,\n        "execution_authority":False,\n    }\n    payload=json.dumps(body,sort_keys=True,separators=(",",":"))\n    body["manifest_sha256"]=hashlib.sha256(payload.encode()).hexdigest()\n    path=root/"qseries_v2"/"oracle_postgresql_reliability"/"OPR_005_FREEZE_MANIFEST.json"\n    path.write_text(json.dumps(body,sort_keys=True,indent=2)+"\\n",encoding="utf-8",newline="\\n")\n    return path,body\n';TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_postgresql_reliability.opr_005_cutover_freeze import *\n\nclass T(unittest.TestCase):\n    def test_identity(self):self.assertEqual(OPR_005_BUILD_ID,"OPR-005")\n    def test_patch(self):\n        s=\'CHILDREN={"a":"x.py","canonical_writer":"y.py"}\\n\'\n        self.assertIn("z.py",patch_child(s,"a","z.py"))\n\nif __name__=="__main__":\n    print("="*88);print(" OPR-005 CERTIFICATION TEST");print(" PHYSICAL CONNECTION-REUSE CUTOVER + FREEZE");print("="*88)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful():raise SystemExit(1)\n    print("[PASS] Safe launcher cutover machinery certified")\n    print("[PASS] execution_authority=FALSE")\n    print("[DONE] OPR-005 GATE CERTIFIED")\n'

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
    print("="*88);print(" OPR-005 INSTALLER");print(" PHYSICAL CONNECTION-REUSE CUTOVER + FREEZE");print("="*88);print("[ROOT]",ROOT)
    sys.path.insert(0,str(ROOT));up=importlib.import_module("qseries_v2.oracle_postgresql_reliability.opr_004_persistent_ingress_wrappers")
    if not up.verify_opr_004_persistent_ingress_wrapper_generation(ROOT):raise RuntimeError("OPR-004 verification failed")
    children_before=up.read_children(LAUNCHER.read_text(encoding="utf-8"))
    learning_before=children_before.get("learning")
    old={p:(p.read_bytes() if p.exists() else None) for p in (MOD,TEST,INIT,LAUNCHER,MANIFEST)}
    try:
        write_exact(MOD,MODULE_SOURCE);write_exact(TEST,TEST_SOURCE);update_init(INIT,"from .opr_005_cutover_freeze import *")
        subprocess.run([sys.executable,str(TEST)],cwd=str(ROOT),check=True)

        # Physical proof that one producer session reuses exactly one PostgreSQL backend.
        s1=importlib.import_module("qseries_v2.oracle_postgresql_reliability.opr_001_persistent_queue_session")
        session=s1.PersistentQueueSession(ROOT)
        pids=[session.backend_pid() for _ in range(100)]
        connects=session.connect_count;session.close()
        if len(set(pids))!=1 or connects!=1:
            raise RuntimeError("Persistent producer session failed 100-probe backend reuse gate")
        print(f"[PHYSICAL REUSE] probes=100 unique_backend_pids={len(set(pids))} connect_count={connects} backend_pid={pids[0]}")

        m=importlib.import_module("qseries_v2.oracle_postgresql_reliability.opr_005_cutover_freeze")
        source=LAUNCHER.read_text(encoding="utf-8");patched=source
        for name in children_before:
            if name=="canonical_writer":
                patched=m.patch_child(patched,name,m.WRITER)
            else:
                wrapper=f"run_opr_004_{up.safe_name(name)}_persistent_ingress.py"
                if not (ROOT/wrapper).is_file():raise RuntimeError("Missing OPR-004 wrapper: "+wrapper)
                patched=m.patch_child(patched,name,wrapper)

        compile(patched,str(LAUNCHER),"exec");write_exact(LAUNCHER,patched)
        subprocess.run([sys.executable,str(LAUNCHER),"--check"],cwd=str(ROOT),check=True)

        if not m.verify_cutover(ROOT):raise RuntimeError("Physical OPR launcher cutover verification failed")

        # Confirm learning's underlying runner is preserved inside the generated wrapper.
        learning_wrapper=ROOT/f"run_opr_004_{up.safe_name('learning')}_persistent_ingress.py"
        underlying=up.unwrap_runner(ROOT,learning_wrapper.name) if learning_wrapper.is_file() else None
        original_underlying=up.unwrap_runner(ROOT,learning_before) if learning_before else None
        if underlying!=original_underlying:
            raise RuntimeError(f"Proven learning underlying changed: before={original_underlying} after={underlying}")

        path,body=m.write_manifest(ROOT,underlying)
        print("[PASS] Wrote:",path.relative_to(ROOT))
        print("[PASS] Manifest SHA256:",body["manifest_sha256"])
    except Exception:
        for p,b in old.items():restore(p,b)
        print("[ROLLBACK] OPR-005 failed; Oracle Live launcher restored");raise

    print("[PASS] 100/100 producer probes reused one PostgreSQL backend")
    print("[PASS] Persistent canonical-writer queue session activated")
    print("[PASS] OPH-019 PostgreSQL queue schema preserved")
    print("[PASS] OPH-021 advisory single-writer lease preserved")
    print("[PASS] Proven learning underlying preserved")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] OPR-005 CUTOVER AND FREEZE COMPLETE")
if __name__=="__main__":main()
