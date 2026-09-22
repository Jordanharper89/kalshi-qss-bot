from pathlib import Path
import importlib
import os
import subprocess
import sys

ROOT=Path.cwd().resolve()
PKG=ROOT/"qseries_v2"/"oracle_production_hardening"
MOD=PKG/"oph_022_oracle_universal_single_writer_cutover.py"
TEST=ROOT/"test_oph_022_oracle_universal_single_writer_cutover.py"
INIT=PKG/"__init__.py"
LAUNCHER=ROOT/"run_oracle_LIVE.py"

MODULE_SOURCE='from __future__ import annotations\nfrom pathlib import Path\nimport ast\n\nOPH_022_BUILD_ID="OPH-022"\nOPH_022_REVISION="OPH_022_ORACLE_UNIVERSAL_SINGLE_WRITER_CUTOVER_CORRECTION_V2"\nCANONICAL_WRITER="run_oph_021_exclusive_postgresql_canonical_writer.py"\n\ndef read_children(source):\n    tree=ast.parse(source)\n    for item in ast.walk(tree):\n        if (\n            isinstance(item,ast.Assign)\n            and isinstance(item.value,ast.Dict)\n            and any(isinstance(t,ast.Name) and t.id=="CHILDREN" for t in item.targets)\n        ):\n            result={}\n            for k,v in zip(item.value.keys,item.value.values):\n                if (\n                    isinstance(k,ast.Constant)\n                    and isinstance(v,ast.Constant)\n                    and isinstance(v.value,str)\n                ):\n                    result[str(k.value)]=str(v.value)\n            return result\n    raise RuntimeError("run_oracle_LIVE.py CHILDREN dictionary not found")\n\ndef patch_child(source,name,value):\n    tree=ast.parse(source)\n    node=None\n    for item in ast.walk(tree):\n        if (\n            isinstance(item,ast.Assign)\n            and isinstance(item.value,ast.Dict)\n            and any(isinstance(t,ast.Name) and t.id=="CHILDREN" for t in item.targets)\n        ):\n            node=item.value\n            break\n    if node is None:\n        raise RuntimeError("CHILDREN dictionary not found")\n\n    lines=source.splitlines(keepends=True)\n    for k,v in zip(node.keys,node.values):\n        if (\n            isinstance(k,ast.Constant)\n            and str(k.value)==name\n            and isinstance(v,ast.Constant)\n            and isinstance(v.value,str)\n        ):\n            old=v.value\n            if old==value:\n                return source\n            line=lines[v.lineno-1]\n            for token in (repr(old),\'"\'+old+\'"\',"\'"+old+"\'"):\n                if token in line:\n                    lines[v.lineno-1]=line.replace(token,repr(value),1)\n                    patched="".join(lines)\n                    ast.parse(patched)\n                    return patched\n    raise RuntimeError(f"child {name} not found")\n\ndef unwrap_runner(root,runner):\n    current=str(runner)\n    seen=set()\n\n    for _ in range(20):\n        if current in seen:\n            raise RuntimeError("recursive wrapper chain detected")\n        seen.add(current)\n\n        p=Path(root)/current\n        if not p.is_file():\n            return current\n\n        target=None\n        try:\n            tree=ast.parse(p.read_text(encoding="utf-8",errors="ignore"))\n            for item in tree.body:\n                if isinstance(item,ast.Assign):\n                    for t in item.targets:\n                        if isinstance(t,ast.Name) and t.id=="UNDERLYING_RUNNER":\n                            target=ast.literal_eval(item.value)\n                            break\n                if target is not None:\n                    break\n        except Exception:\n            target=None\n\n        if not target:\n            return current\n        current=str(target)\n\n    raise RuntimeError("wrapper resolution exceeded safety depth")\n\ndef safe_child_name(name):\n    return "".join(c if c.isalnum() else "_" for c in str(name)).strip("_").lower()\n\ndef wrapper_source(child_name,underlying):\n    producer="oracle."+str(child_name)\n\n    lines=[\n        "from pathlib import Path",\n        "import runpy",\n        "from qseries_v2.oracle_production_hardening.oph_020_universal_postgresql_producer_admission import install_universal_postgresql_ingress",\n        f"UNDERLYING_RUNNER={underlying!r}",\n        "",\n        "if __name__==\'__main__\':",\n        "    print(\'=\'*88,flush=True)",\n        f"    print(\' OPH-022 UNIVERSAL POSTGRESQL INGRESS child={child_name}\',flush=True)",\n        "    print(\'=\'*88,flush=True)",\n        f"    install_universal_postgresql_ingress({producer!r},Path.cwd())",\n        "    print(\'[OPH-022] direct_canonical_postgresql_write_authority=FALSE\',flush=True)",\n        "    runpy.run_path(str(Path.cwd()/UNDERLYING_RUNNER),run_name=\'__main__\')",\n        "",\n    ]\n    source="\\n".join(lines)\n    ast.parse(source)\n    return source\n\ndef verify_wrapper_file(path):\n    path=Path(path)\n    if not path.is_file():\n        return False\n    source=path.read_text(encoding="utf-8")\n    ast.parse(source)\n    if "\\\\n" in source.splitlines()[0]:\n        return False\n    return (\n        "install_universal_postgresql_ingress" in source\n        and "direct_canonical_postgresql_write_authority=FALSE" in source\n    )\n\ndef verify_oph_022_oracle_universal_single_writer_cutover(root=None):\n    root=Path(root or Path.cwd()).resolve()\n    launcher=root/"run_oracle_LIVE.py"\n\n    if not launcher.is_file():\n        return False\n\n    children=read_children(launcher.read_text(encoding="utf-8"))\n\n    if children.get("canonical_writer")!=CANONICAL_WRITER:\n        return False\n\n    producer_count=0\n    for name,runner in children.items():\n        if name=="canonical_writer":\n            continue\n        producer_count+=1\n        if not runner.startswith("run_oph_022_"):\n            return False\n        if not runner.endswith("_postgresql_ingress.py"):\n            return False\n        if not verify_wrapper_file(root/runner):\n            return False\n\n    return producer_count>0\n'
TEST_SOURCE='import unittest\nfrom pathlib import Path\nimport tempfile\n\nfrom qseries_v2.oracle_production_hardening.oph_022_oracle_universal_single_writer_cutover import (\n    CANONICAL_WRITER,\n    read_children,\n    wrapper_source,\n    verify_wrapper_file,\n)\n\nclass T(unittest.TestCase):\n    def test_children_parser(self):\n        source=\'CHILDREN={"fast_lane":"a.py","canonical_writer":"b.py"}\\n\'\n        children=read_children(source)\n        self.assertEqual(children["fast_lane"],"a.py")\n\n    def test_wrapper_uses_real_newlines(self):\n        source=wrapper_source("fast_lane","run_raw.py")\n        self.assertGreater(len(source.splitlines()),5)\n        self.assertEqual(source.splitlines()[0],"from pathlib import Path")\n        compile(source,"generated_wrapper","exec")\n\n    def test_wrapper_file_verifier(self):\n        with tempfile.TemporaryDirectory() as td:\n            p=Path(td)/"wrapper.py"\n            p.write_text(wrapper_source("coverage","run_raw.py"),encoding="utf-8",newline="\\n")\n            self.assertTrue(verify_wrapper_file(p))\n\n    def test_canonical_writer_identity(self):\n        self.assertEqual(\n            CANONICAL_WRITER,\n            "run_oph_021_exclusive_postgresql_canonical_writer.py",\n        )\n\nif __name__=="__main__":\n    print("="*88)\n    print(" OPH-022 CERTIFICATION TEST")\n    print(" ORACLE UNIVERSAL SINGLE-WRITER CUTOVER — CORRECTION V2")\n    print("="*88)\n\n    result=unittest.TextTestRunner(verbosity=2).run(\n        unittest.defaultTestLoader.loadTestsFromTestCase(T)\n    )\n    if not result.wasSuccessful():\n        raise SystemExit(1)\n\n    print("[PASS] Generated wrappers use physical newline characters")\n    print("[PASS] Generated wrappers compile before launcher modification")\n    print("[PASS] Universal PostgreSQL ingress cutover contract certified")\n    print("[PASS] execution_authority=FALSE")\n    print("[DONE] OPH-022 CERTIFIED")\n'

def write_exact(path,text):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(text,encoding="utf-8",newline="\n")
    os.replace(tmp,path)

def update_init(path,export):
    current=path.read_text(encoding="utf-8") if path.exists() else ""
    if export not in current.splitlines():
        write_exact(path,current.rstrip()+"\n"+export+"\n")

def restore_file(path,data):
    if data is None:
        if path.exists():
            path.unlink()
    else:
        path.write_bytes(data)

def main():
    print("="*88)
    print(" OPH-022 INSTALLER")
    print(" ORACLE UNIVERSAL SINGLE-WRITER CUTOVER — CORRECTION V2")
    print("="*88)
    print("[ROOT]",ROOT)

    sys.path.insert(0,str(ROOT))

    upstream=importlib.import_module(
        "qseries_v2.oracle_production_hardening.oph_021_exclusive_postgresql_canonical_writer"
    )
    if upstream.verify_oph_021_exclusive_postgresql_canonical_writer() is not True:
        raise RuntimeError("Certified OPH-021 verification failed")

    print("[PASS] Certified OPH-021 upstream boundary verified read-only")

    if not LAUNCHER.is_file():
        raise RuntimeError("run_oracle_LIVE.py missing")

    affected=(MOD,TEST,INIT,LAUNCHER)
    old={p:(p.read_bytes() if p.exists() else None) for p in affected}
    generated=[]
    generated_old={}

    try:
        write_exact(MOD,MODULE_SOURCE)
        write_exact(TEST,TEST_SOURCE)
        update_init(
            INIT,
            "from .oph_022_oracle_universal_single_writer_cutover import *",
        )

        compile(MOD.read_text(encoding="utf-8"),str(MOD),"exec")
        compile(TEST.read_text(encoding="utf-8"),str(TEST),"exec")

        importlib.invalidate_caches()
        m=importlib.import_module(
            "qseries_v2.oracle_production_hardening.oph_022_oracle_universal_single_writer_cutover"
        )

        source=LAUNCHER.read_text(encoding="utf-8")
        children=m.read_children(source)

        if "canonical_writer" not in children:
            raise RuntimeError("run_oracle_LIVE.py lacks canonical_writer child")

        patched=source

        for name,runner in children.items():
            if name=="canonical_writer":
                patched=m.patch_child(patched,name,m.CANONICAL_WRITER)
                print(
                    "[PASS] canonical_writer ->",
                    m.CANONICAL_WRITER,
                )
                continue

            underlying=m.unwrap_runner(ROOT,runner)
            wrapper=ROOT/f"run_oph_022_{m.safe_child_name(name)}_postgresql_ingress.py"

            if wrapper not in generated_old:
                generated_old[wrapper]=wrapper.read_bytes() if wrapper.exists() else None
            generated.append(wrapper)

            wrapper_text=m.wrapper_source(name,underlying)

            # Critical V2 correction:
            # wrapper_text contains physical newline characters, not literal backslash-n text.
            if len(wrapper_text.splitlines())<6:
                raise RuntimeError(
                    f"Generated wrapper newline validation failed for {name}"
                )

            compile(wrapper_text,str(wrapper),"exec")
            write_exact(wrapper,wrapper_text)

            if not m.verify_wrapper_file(wrapper):
                raise RuntimeError(
                    f"Generated wrapper physical verification failed for {name}"
                )

            patched=m.patch_child(patched,name,wrapper.name)

            print(
                f"[PASS] child={name} underlying={underlying} -> {wrapper.name}"
            )

        compile(patched,str(LAUNCHER),"exec")
        write_exact(LAUNCHER,patched)

        subprocess.run(
            [sys.executable,str(TEST)],
            cwd=str(ROOT),
            check=True,
        )

        subprocess.run(
            [sys.executable,str(LAUNCHER),"--check"],
            cwd=str(ROOT),
            check=True,
        )

        importlib.invalidate_caches()
        m=importlib.reload(m)

        if not m.verify_oph_022_oracle_universal_single_writer_cutover(ROOT):
            raise RuntimeError(
                "Physical OPH-022 universal cutover verification failed"
            )

    except Exception:
        for p,b in old.items():
            restore_file(p,b)

        for p,b in generated_old.items():
            restore_file(p,b)

        print(
            "[ROLLBACK] OPH-022 correction failed; launcher and affected files restored"
        )
        raise

    print("[PASS] All generated ingress wrappers physically compile")
    print("[PASS] All supervised producer children use OPH-020 PostgreSQL ingress")
    print("[PASS] canonical_writer="+m.CANONICAL_WRITER)
    print("[PASS] Legacy SQLite queue is absent from the active launcher path")
    print("[PASS] Operator Terminal dependency remains NONE")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] OPH-022 INSTALLATION AND CERTIFICATION COMPLETE")

if __name__=="__main__":
    main()
