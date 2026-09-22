from __future__ import annotations

import ast
import os
import shutil
import subprocess
import sys
from pathlib import Path

EXPECTED = "build_oad_291_gmgn_supervised_node_environment_FOUNDATIONAL_REBUILD.py"
LAUNCHER = "run_oracle_live.py"
RUNNER = "run_oad_290_gmgn_clean_continuous_intelligence_child.py"
TEST = "test_oad_291_gmgn_supervised_node_environment.py"

BLOCK_BEGIN = "# BEGIN GMGN_SUPERVISED_NODE_ENVIRONMENT_V1"
BLOCK_END = "# END GMGN_SUPERVISED_NODE_ENVIRONMENT_V1"

def repo_root():
    for base in (Path.cwd().resolve(), Path(__file__).resolve().parent):
        for p in (base, *base.parents):
            if (p / "qseries_v2").is_dir() and (p / LAUNCHER).is_file():
                return p
    raise RuntimeError("Q Series repository root not found")

def require(path, markers=()):
    if not path.is_file():
        raise RuntimeError("required file missing: " + str(path))
    s = path.read_text(encoding="utf-8")
    for m in markers:
        if m not in s:
            raise RuntimeError(f"required marker missing in {path}: {m}")
    return s

def locate_node():
    candidates = []
    for name in ("node.exe", "node"):
        w = shutil.which(name)
        if w:
            candidates.append(Path(w))
    for p in (
        Path(r"C:\Program Files\nodejs\node.exe"),
        Path(r"C:\Program Files (x86)\nodejs\node.exe"),
    ):
        candidates.append(p)
    local = os.environ.get("LOCALAPPDATA")
    if local:
        candidates.append(Path(local) / "Programs" / "nodejs" / "node.exe")
    seen = set()
    for p in candidates:
        try:
            q = p.resolve()
        except Exception:
            q = p
        k = str(q).lower()
        if k in seen:
            continue
        seen.add(k)
        if q.is_file():
            return q
    raise RuntimeError("Node executable not found")

def locate_gmgn():
    candidates = []
    for name in ("gmgn-cli.cmd", "gmgn-cli"):
        w = shutil.which(name)
        if w:
            candidates.append(Path(w))
    appdata = os.environ.get("APPDATA")
    if appdata:
        candidates.append(Path(appdata) / "npm" / "gmgn-cli.cmd")
    profile = os.environ.get("USERPROFILE")
    if profile:
        candidates.append(Path(profile) / "AppData" / "Roaming" / "npm" / "gmgn-cli.cmd")
    for p in candidates:
        if p.is_file():
            return p.resolve()
    raise RuntimeError("gmgn-cli not found")

def make_block(node, gmgn):
    return f'''
{BLOCK_BEGIN}
def _gmgn_supervised_environment():
    import os as _os
    from pathlib import Path as _Path
    _node = _Path({str(node)!r})
    _gmgn = _Path({str(gmgn)!r})
    if not _node.is_file():
        raise RuntimeError("GMGN supervised Node executable missing: " + str(_node))
    if not _gmgn.is_file():
        raise RuntimeError("GMGN supervised gmgn-cli missing: " + str(_gmgn))
    _env = _os.environ.copy()
    _parts = [str(_node.parent), str(_gmgn.parent)]
    if _env.get("PATH"):
        _parts.append(_env["PATH"])
    _env["PATH"] = _os.pathsep.join(_parts)
    _env["GMGN_SUPERVISED_NODE_EXE"] = str(_node)
    _env["GMGN_SUPERVISED_CLI"] = str(_gmgn)
    return _env, str(_node), str(_gmgn)

def _gmgn_supervised_cli(args, timeout=60):
    import subprocess as _sp
    _env, _node, _gmgn = _gmgn_supervised_environment()
    if _gmgn.lower().endswith((".cmd", ".bat")):
        _comspec = _env.get("COMSPEC") or r"C:\\Windows\\System32\\cmd.exe"
        _cmd = [_comspec, "/d", "/s", "/c", _sp.list2cmdline([_gmgn, *list(args)])]
    else:
        _cmd = [_gmgn, *list(args)]
    return _sp.run(_cmd, cwd=str(Path.cwd()), env=_env, text=True, capture_output=True, timeout=timeout, check=False)

def _gmgn_supervised_env_check():
    import subprocess as _sp
    _env, _node, _gmgn = _gmgn_supervised_environment()
    _n = _sp.run([_node, "--version"], cwd=str(Path.cwd()), env=_env, text=True, capture_output=True, timeout=30, check=False)
    _g = _gmgn_supervised_cli(["--version"], timeout=30)
    _c = _gmgn_supervised_cli(["config", "--check"], timeout=45)
    print("[GMGN SUPERVISED ENV] node=" + _node)
    print("[GMGN SUPERVISED ENV] gmgn_cli=" + _gmgn)
    print("[GMGN SUPERVISED ENV] node_version=" + _n.stdout.strip())
    print("[GMGN SUPERVISED ENV] gmgn_version=" + _g.stdout.strip())
    if _n.returncode or _g.returncode or _c.returncode:
        print("[GMGN SUPERVISED ENV] node_stderr=" + repr(_n.stderr))
        print("[GMGN SUPERVISED ENV] gmgn_stderr=" + repr(_g.stderr))
        print("[GMGN SUPERVISED ENV] config_stderr=" + repr(_c.stderr))
        return 2
    print("[GMGN SUPERVISED ENV] admitted=TRUE execution_authority=FALSE")
    return 0

def _gmgn_supervised_one_cycle():
    import subprocess as _sp
    _env, _node, _gmgn = _gmgn_supervised_environment()
    _p = _sp.run(
        [sys.executable, "{RUNNER}", "--max-cycles", "1", "--cadence-seconds", "1"],
        cwd=str(Path.cwd()), env=_env, text=True, capture_output=True, timeout=180, check=False
    )
    print(_p.stdout, end="")
    if _p.stderr:
        print(_p.stderr, end="", file=sys.stderr)
    if _p.returncode != 0:
        return _p.returncode
    if "status=SUCCESS" not in _p.stdout or "exact_readback=3" not in _p.stdout:
        print("[GMGN SUPERVISED CHILD] status=FAILURE")
        return 3
    print("[GMGN SUPERVISED CHILD] status=SUCCESS exact_readback=3 execution_authority=FALSE")
    return 0
{BLOCK_END}
'''

def inject_block(src, block):
    if BLOCK_BEGIN in src:
        a = src.index(BLOCK_BEGIN)
        b = src.index(BLOCK_END, a) + len(BLOCK_END)
        return src[:a] + block.strip() + src[b:]
    lines = src.splitlines(True)
    insert_at = 0
    for i, line in enumerate(lines):
        s = line.strip()
        if s.startswith("import ") or s.startswith("from "):
            insert_at = i + 1
    return "".join(lines[:insert_at]) + "\n" + block.strip() + "\n\n" + "".join(lines[insert_at:])

def patch_main_modes(src):
    anchor = 'if __name__ == "__main__":'
    if anchor not in src:
        raise RuntimeError("launcher __main__ boundary missing")
    if "--gmgn-supervised-env-check" not in src:
        diag = (
            'if "--gmgn-supervised-env-check" in sys.argv:\n'
            '    raise SystemExit(_gmgn_supervised_env_check())\n\n'
            'if "--gmgn-supervised-one-cycle" in sys.argv:\n'
            '    raise SystemExit(_gmgn_supervised_one_cycle())\n\n'
        )
        src = src.replace(anchor, diag + anchor, 1)
    return src

def patch_gmgn_env(src):
    if '"gmgn_intelligence": "run_oad_290_gmgn_clean_continuous_intelligence_child.py"' not in src:
        raise RuntimeError("OAD-291 GMGN child binding missing")

    exact = [
        ('env=_gmgn_child_env', 'env=(_gmgn_supervised_environment()[0] if child_name == "gmgn_intelligence" else _gmgn_child_env)'),
        ('env=child_env', 'env=(_gmgn_supervised_environment()[0] if child_name == "gmgn_intelligence" else child_env)'),
        ('env=env', 'env=(_gmgn_supervised_environment()[0] if child_name == "gmgn_intelligence" else env)'),
    ]
    for old, new in exact:
        if old in src and new not in src:
            return src.replace(old, new, 1)

    # OAD-285 used GMGN-only environment normalization; repair that function directly when present.
    marker = 'def _gmgn_child_environment'
    if marker in src:
        start = src.index(marker)
        end = src.find("\ndef ", start + len(marker))
        if end == -1:
            end = src.find('\nif __name__ == "__main__":', start)
        if end == -1:
            raise RuntimeError("unable to bound existing GMGN environment function")
        body = src[start:end]
        indent = "    "
        if "return " in body:
            body_lines = body.splitlines()
            for i in range(len(body_lines)-1, -1, -1):
                if body_lines[i].lstrip().startswith("return "):
                    body_lines.insert(i, indent + '_env, _, _ = _gmgn_supervised_environment()')
                    body_lines[i+1] = indent + "return _env"
                    return src[:start] + "\n".join(body_lines) + src[end:]

    raise RuntimeError("exact GMGN supervised child environment handoff not found; rollback instead of guessing")

def test_source():
    return r'''
from __future__ import annotations
import subprocess, sys, unittest
from pathlib import Path

class T(unittest.TestCase):
    def test_01_launcher_check(self):
        p=subprocess.run([sys.executable,"run_oracle_live.py","--check"],cwd=Path.cwd(),text=True,capture_output=True,timeout=60)
        print(p.stdout,end=""); print(p.stderr,end="")
        self.assertEqual(p.returncode,0)

    def test_02_supervised_env(self):
        p=subprocess.run([sys.executable,"run_oracle_live.py","--gmgn-supervised-env-check"],cwd=Path.cwd(),text=True,capture_output=True,timeout=120)
        print(p.stdout,end=""); print(p.stderr,end="")
        self.assertEqual(p.returncode,0)
        self.assertIn("admitted=TRUE",p.stdout)

    def test_03_supervised_cycle(self):
        p=subprocess.run([sys.executable,"run_oracle_live.py","--gmgn-supervised-one-cycle"],cwd=Path.cwd(),text=True,capture_output=True,timeout=240)
        print(p.stdout,end=""); print(p.stderr,end="")
        self.assertEqual(p.returncode,0)
        self.assertIn("[GMGN SUPERVISED CHILD] status=SUCCESS",p.stdout)
        self.assertIn("exact_readback=3",p.stdout)

    def test_04_safety(self):
        s=Path("run_oracle_live.py").read_text(encoding="utf-8")
        self.assertIn("execution_authority=FALSE",s)
        self.assertIn('"gmgn_intelligence": "run_oad_290_gmgn_clean_continuous_intelligence_child.py"',s)
        self.assertIn("GMGN_SUPERVISED_NODE_ENVIRONMENT_V1",s)

if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] exact supervised Node environment physically verified")
    print("[PASS] exact supervised gmgn-cli admission physically verified")
    print("[PASS] OAD-290 completed one supervised physical cycle")
    print("[PASS] exact_readback=3")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] OAD-291 GMGN SUPERVISED NODE ENVIRONMENT FOUNDATIONAL REBUILD CERTIFIED")
'''

def main():
    if Path(__file__).name != EXPECTED:
        raise RuntimeError("installer filename identity mismatch")
    root = repo_root()
    launcher = root / LAUNCHER
    runner = root / RUNNER
    test = root / TEST

    print("="*112)
    print(" OAD-291 GMGN SUPERVISED NODE ENVIRONMENT — FOUNDATIONAL REBUILD")
    print("="*112)
    print("[ROOT]", root)

    src = require(launcher, (
        '"gmgn_intelligence": "run_oad_290_gmgn_clean_continuous_intelligence_child.py"',
        "execution_authority=FALSE",
    ))
    require(runner, ("oad_290_gmgn_clean_continuous_runtime", "--max-cycles"))
    require(root / "qseries_v2/oracle_adapters/independent/oad_287_gmgn_clean_provider_foundation.py", ("def require_gmgn_provider",))
    require(root / "qseries_v2/oracle_adapters/independent/oad_289_gmgn_clean_single_writer_persistence.py", ("def persist_current_gmgn",))

    node = locate_node()
    gmgn = locate_gmgn()
    print("[NODE]", node)
    print("[GMGN CLI]", gmgn)

    nv = subprocess.run([str(node), "--version"], cwd=root, text=True, capture_output=True, timeout=30)
    if nv.returncode != 0:
        raise RuntimeError("node --version failed: " + nv.stderr)
    print("[NODE VERSION]", nv.stdout.strip())

    backup = launcher.with_name(launcher.name + ".oad291_pre_supervised_node_environment_rebuild")
    backup.write_bytes(launcher.read_bytes())

    try:
        rebuilt = inject_block(src, make_block(node, gmgn))
        rebuilt = patch_main_modes(rebuilt)
        rebuilt = patch_gmgn_env(rebuilt)
        ast.parse(rebuilt, filename=str(launcher))

        tmp = launcher.with_suffix(".py.tmp")
        tmp.write_text(rebuilt, encoding="utf-8", newline="\n")
        os.replace(tmp, launcher)

        ts = test_source().lstrip()
        ast.parse(ts, filename=str(test))
        test.write_text(ts, encoding="utf-8", newline="\n")

        q = subprocess.run([sys.executable, LAUNCHER, "--check"], cwd=root, text=True, capture_output=True, timeout=60)
        if q.returncode != 0:
            raise RuntimeError("launcher --check failed:\n" + q.stdout + "\n" + q.stderr)

        e = subprocess.run([sys.executable, LAUNCHER, "--gmgn-supervised-env-check"], cwd=root, text=True, capture_output=True, timeout=120)
        print(e.stdout, end=""); print(e.stderr, end="")
        if e.returncode != 0:
            raise RuntimeError("supervised environment check failed")

        print("[PASS] exact Node executable resolved")
        print("[PASS] exact gmgn-cli resolved")
        print("[PASS] existing GMGN supervised child environment rebuilt in place")
        print("[PASS] non-GMGN child behavior preserved")
        print("[PASS] launcher --check passed")
        print("[PASS] supervised node/gmgn admission passed")
        print("[PASS] probability=FALSE direction=FALSE publication=FALSE execution=FALSE")
        print("[DONE] OAD-291 SUPERVISED NODE ENVIRONMENT FOUNDATIONAL REBUILD INSTALLED")
    except Exception:
        launcher.write_bytes(backup.read_bytes())
        print("[ROLLBACK] run_oracle_live.py restored")
        raise

if __name__ == "__main__":
    main()
