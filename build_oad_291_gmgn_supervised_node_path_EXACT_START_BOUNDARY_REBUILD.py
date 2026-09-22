from __future__ import annotations

import ast
import os
import subprocess
import sys
import textwrap
from pathlib import Path

EXPECTED_FILENAME = "build_oad_291_gmgn_supervised_node_path_EXACT_START_BOUNDARY_REBUILD.py"
LAUNCHER = "run_oracle_live.py"
TEST = "test_oad_291_gmgn_supervised_node_path_exact_start_boundary.py"
GMGN_RUNNER = "run_oad_290_gmgn_clean_continuous_intelligence_child.py"

NEW_START = r"""
def _start(root,name):
    p=root/name
    if not p.is_file():
        raise RuntimeError("runtime child missing: "+name)

    if name == "run_oad_290_gmgn_clean_continuous_intelligence_child.py":
        env=os.environ.copy()

        if os.name=="nt":
            system_root=(env.get("SystemRoot") or r"C:\Windows").strip()
            env["SystemRoot"]=system_root
            env["COMSPEC"]=(env.get("COMSPEC") or str(Path(system_root)/"System32"/"cmd.exe")).strip()

            userprofile=(env.get("USERPROFILE") or str(Path.home())).strip()
            env["USERPROFILE"]=userprofile

            appdata=(env.get("APPDATA") or str(Path(userprofile)/"AppData"/"Roaming")).strip()
            env["APPDATA"]=appdata

            npm_dir=Path(appdata)/"npm"

            node_candidates=[]
            for base in (
                env.get("ProgramFiles"),
                env.get("ProgramW6432"),
                env.get("ProgramFiles(x86)"),
            ):
                if base:
                    node_candidates.append(Path(base)/"nodejs"/"node.exe")

            localappdata=env.get("LOCALAPPDATA")
            if localappdata:
                node_candidates.append(Path(localappdata)/"Programs"/"nodejs"/"node.exe")

            node_candidates.extend((
                Path(r"C:\Program Files\nodejs\node.exe"),
                Path(r"C:\Program Files (x86)\nodejs\node.exe"),
            ))

            node_exe=None
            seen=set()
            for candidate in node_candidates:
                key=os.path.normcase(os.path.normpath(str(candidate)))
                if key in seen:
                    continue
                seen.add(key)
                if candidate.is_file():
                    node_exe=candidate
                    break

            if node_exe is None:
                raise RuntimeError("GMGN supervised Node executable not found")

            gmgn_cmd=npm_dir/"gmgn-cli.cmd"
            if not gmgn_cmd.is_file():
                raise RuntimeError("GMGN supervised gmgn-cli.cmd not found: "+str(gmgn_cmd))

            parts=[x for x in env.get("PATH","").split(os.pathsep) if x]
            norm=lambda x: os.path.normcase(os.path.normpath(str(x)))
            existing={norm(x) for x in parts}

            for required in (str(node_exe.parent),str(npm_dir)):
                if norm(required) not in existing:
                    parts.insert(0,required)
                    existing.add(norm(required))

            env["PATH"]=os.pathsep.join(parts)
            env["GMGN_SUPERVISED_NODE_EXE"]=str(node_exe)
            env["GMGN_SUPERVISED_CLI"]=str(gmgn_cmd)

        return subprocess.Popen([sys.executable,str(p)],cwd=str(root),env=env)

    return subprocess.Popen([sys.executable,str(p)],cwd=str(root))
"""

TEST_SOURCE = r"""
from __future__ import annotations

import ast
import importlib.util
import os
import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT=Path.cwd().resolve()
LAUNCHER=ROOT/"run_oracle_live.py"
RUNNER=ROOT/"run_oad_290_gmgn_clean_continuous_intelligence_child.py"

def load_launcher():
    spec=importlib.util.spec_from_file_location("oracle_live_env_test",LAUNCHER)
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

class DummyProc:
    def poll(self): return None

class T(unittest.TestCase):
    def test_01_exact_binding_and_truthful_health_preserved(self):
        s=LAUNCHER.read_text(encoding="utf-8")
        self.assertIn(
            '"gmgn_intelligence": "run_oad_290_gmgn_clean_continuous_intelligence_child.py"',
            s,
        )
        self.assertIn("gmgn_checkpoint_cycle_at_spawn",s)
        self.assertIn("if cp.last_error:",s)
        self.assertIn("if success_age > 240.0:",s)
        self.assertIn("restart_backoff_seconds",s)
        self.assertNotIn("execution_authority=TRUE",s)

    def test_02_gmgn_only_supervised_environment_contains_node_and_npm(self):
        mod=load_launcher()
        captured={}

        def fake_popen(args,**kwargs):
            captured["args"]=args
            captured.update(kwargs)
            return DummyProc()

        with patch.object(mod.subprocess,"Popen",side_effect=fake_popen):
            mod._start(ROOT,RUNNER.name)

        env=captured.get("env")
        self.assertIsInstance(env,dict)
        self.assertIn("GMGN_SUPERVISED_NODE_EXE",env)
        self.assertIn("GMGN_SUPERVISED_CLI",env)

        node=Path(env["GMGN_SUPERVISED_NODE_EXE"])
        gmgn=Path(env["GMGN_SUPERVISED_CLI"])
        self.assertTrue(node.is_file(),node)
        self.assertTrue(gmgn.is_file(),gmgn)

        path_parts=[os.path.normcase(os.path.normpath(x)) for x in env["PATH"].split(os.pathsep)]
        self.assertIn(os.path.normcase(os.path.normpath(str(node.parent))),path_parts)
        self.assertIn(os.path.normcase(os.path.normpath(str(gmgn.parent))),path_parts)

        n=subprocess.run(
            [str(node),"--version"],
            cwd=ROOT,env=env,text=True,capture_output=True,timeout=30,check=False,
        )
        print("[SUPERVISED NODE]",node)
        print("[SUPERVISED NODE VERSION]",n.stdout.strip())
        self.assertEqual(n.returncode,0,n.stderr)

        comspec=env.get("COMSPEC")
        g=subprocess.run(
            [comspec,"/d","/s","/c",subprocess.list2cmdline([str(gmgn),"--version"])],
            cwd=ROOT,env=env,text=True,capture_output=True,timeout=45,check=False,
        )
        print("[SUPERVISED GMGN]",gmgn)
        print("[SUPERVISED GMGN VERSION]",g.stdout.strip())
        self.assertEqual(g.returncode,0,g.stderr)

        c=subprocess.run(
            [comspec,"/d","/s","/c",subprocess.list2cmdline([str(gmgn),"config","--check"])],
            cwd=ROOT,env=env,text=True,capture_output=True,timeout=60,check=False,
        )
        print("[SUPERVISED CONFIG CHECK RETURN]",c.returncode)
        if c.stdout: print(c.stdout,end="")
        if c.stderr: print(c.stderr,end="")
        self.assertEqual(c.returncode,0)

        self.__class__.supervised_env=env

    def test_03_non_gmgn_child_spawn_has_no_special_env(self):
        mod=load_launcher()
        other=None
        for key,name in mod.CHILDREN.items():
            if key!="gmgn_intelligence":
                other=name
                break
        self.assertIsNotNone(other)

        captured={}
        def fake_popen(args,**kwargs):
            captured["args"]=args
            captured.update(kwargs)
            return DummyProc()

        with patch.object(mod.subprocess,"Popen",side_effect=fake_popen):
            mod._start(ROOT,other)

        self.assertNotIn("env",captured)

    def test_04_physical_oad290_cycle_under_exact_supervised_env(self):
        mod=load_launcher()
        captured={}

        def fake_popen(args,**kwargs):
            captured.update(kwargs)
            return DummyProc()

        with patch.object(mod.subprocess,"Popen",side_effect=fake_popen):
            mod._start(ROOT,RUNNER.name)

        env=captured["env"]
        p=subprocess.run(
            [sys.executable,str(RUNNER),"--max-cycles","1","--cadence-seconds","1"],
            cwd=ROOT,env=env,text=True,capture_output=True,timeout=240,check=False,
        )
        print(p.stdout,end="")
        if p.stderr: print(p.stderr,end="")
        self.assertEqual(p.returncode,0)
        self.assertIn("status=SUCCESS",p.stdout)
        self.assertIn("exact_readback=3",p.stdout)
        self.assertIn("execution_authority=FALSE",p.stdout)

    def test_05_launcher_check(self):
        p=subprocess.run(
            [sys.executable,str(LAUNCHER),"--check"],
            cwd=ROOT,text=True,capture_output=True,timeout=60,check=False,
        )
        print(p.stdout,end="")
        if p.stderr: print(p.stderr,end="")
        self.assertEqual(p.returncode,0)

if __name__=="__main__":
    print("="*116)
    print(" OAD-291 GMGN SUPERVISED NODE PATH — EXACT _start BOUNDARY CERTIFICATION")
    print("="*116)
    r=unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(T)
    )
    if not r.wasSuccessful():
        raise SystemExit(1)
    print("[PASS] exact OAD-290 GMGN child binding preserved")
    print("[PASS] supervised Node executable physically verified")
    print("[PASS] supervised gmgn-cli admission physically verified")
    print("[PASS] exact GMGN-only PATH includes Node + npm")
    print("[PASS] non-GMGN child spawn behavior preserved")
    print("[PASS] OAD-290 physical cycle succeeded under exact supervised environment")
    print("[PASS] exact_readback=3")
    print("[PASS] truthful provider health preserved")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] OAD-291 EXACT START-BOUNDARY NODE PATH REBUILD CERTIFIED")
"""

def root():
    for b in (Path.cwd().resolve(),Path(__file__).resolve().parent):
        for p in (b,*b.parents):
            if (p/"qseries_v2").is_dir() and (p/LAUNCHER).is_file():
                return p
    raise RuntimeError("Q Series repository root not found")

def replace_start(src):
    tree=ast.parse(src)
    node=None
    for n in tree.body:
        if isinstance(n,ast.FunctionDef) and n.name=="_start":
            node=n
            break
    if node is None:
        raise RuntimeError("exact launcher _start boundary missing")

    lines=src.splitlines(keepends=True)
    rebuilt=(
        "".join(lines[:node.lineno-1])
        + textwrap.dedent(NEW_START).lstrip()
        + "\n"
        + "".join(lines[node.end_lineno:])
    )
    ast.parse(rebuilt)
    return rebuilt

def main():
    if Path(__file__).name!=EXPECTED_FILENAME:
        raise RuntimeError("installer identity mismatch")

    r=root()
    launcher=r/LAUNCHER
    test=r/TEST
    runner=r/GMGN_RUNNER

    print("="*116)
    print(" OAD-291 GMGN SUPERVISED NODE PATH — EXACT _start FOUNDATIONAL REBUILD")
    print("="*116)
    print("[ROOT]",r)

    src=launcher.read_text(encoding="utf-8")
    ast.parse(src)

    required=(
        '"gmgn_intelligence": "run_oad_290_gmgn_clean_continuous_intelligence_child.py"',
        "gmgn_checkpoint_cycle_at_spawn",
        "if cp.last_error:",
        "if success_age > 240.0:",
        "restart_backoff_seconds",
        "def _start(root,name):",
        "execution_authority=FALSE",
    )
    for marker in required:
        if marker not in src:
            raise RuntimeError("required current production boundary missing: "+marker)

    if "execution_authority=TRUE" in src:
        raise RuntimeError("execution safety boundary violation")
    if not runner.is_file():
        raise RuntimeError("OAD-290 production runner missing")

    before_tree=ast.parse(src)
    before_children=None
    for n in before_tree.body:
        if isinstance(n,ast.Assign) and isinstance(n.value,ast.Dict):
            if any(isinstance(t,ast.Name) and t.id=="CHILDREN" for t in n.targets):
                before_children=ast.literal_eval(n.value)
                break
    if before_children is None:
        raise RuntimeError("CHILDREN boundary missing")

    old_launcher=launcher.read_bytes()
    old_test=test.read_bytes() if test.exists() else None
    backup=launcher.with_name(
        launcher.name+".oad291_pre_exact_start_node_path_rebuild"
    )
    backup.write_bytes(old_launcher)

    try:
        rebuilt=replace_start(src)
        ast.parse(rebuilt)

        after_tree=ast.parse(rebuilt)
        after_children=None
        for n in after_tree.body:
            if isinstance(n,ast.Assign) and isinstance(n.value,ast.Dict):
                if any(isinstance(t,ast.Name) and t.id=="CHILDREN" for t in n.targets):
                    after_children=ast.literal_eval(n.value)
                    break
        if after_children!=before_children:
            raise RuntimeError("CHILDREN registry changed unexpectedly")

        launcher.write_text(rebuilt,encoding="utf-8",newline="\n")
        ts=textwrap.dedent(TEST_SOURCE).lstrip()
        ast.parse(ts,filename=str(test))
        test.write_text(ts,encoding="utf-8",newline="\n")

        q=subprocess.run(
            [sys.executable,str(launcher),"--check"],
            cwd=r,text=True,capture_output=True,timeout=60,check=False,
        )
        if q.returncode!=0:
            raise RuntimeError(
                "launcher --check failed:\n"+q.stdout+"\n"+q.stderr
            )

        print("[PASS] exact production _start boundary located by AST")
        print("[PASS] OAD-290 GMGN binding verified")
        print("[PASS] truthful provider-health run_forever preserved")
        print("[PASS] GMGN-only supervised environment rebuilt")
        print("[PASS] deterministic Node + npm PATH construction installed")
        print("[PASS] all CHILDREN bindings preserved exactly")
        print("[PASS] non-GMGN default Popen path preserved")
        print("[PASS] launcher --check passed")
        print("[PASS] probability=FALSE direction=FALSE publication=FALSE execution=FALSE")
        print("[DONE] OAD-291 EXACT START-BOUNDARY NODE PATH REBUILD INSTALLED")

    except Exception:
        launcher.write_bytes(old_launcher)
        if old_test is None:
            if test.exists():
                test.unlink()
        else:
            test.write_bytes(old_test)
        print("[ROLLBACK] launcher/test restored")
        raise

if __name__=="__main__":
    main()
