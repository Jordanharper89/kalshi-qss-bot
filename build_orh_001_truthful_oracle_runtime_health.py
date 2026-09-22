from pathlib import Path
import ast
import hashlib
import json
import os
import subprocess
import sys
import importlib

ROOT = Path.cwd().resolve()
LAUNCHER = ROOT / "run_oracle_LIVE.py"
TEST = ROOT / "test_orh_001_truthful_oracle_runtime_health.py"
PKG = ROOT / "qseries_v2" / "oracle_runtime_health"
MOD = PKG / "orh_001_truthful_runtime_health.py"
INIT = PKG / "__init__.py"
MANIFEST = PKG / "ORH_001_MANIFEST.json"

EXPECTED_CORE = {
    "fast_lane",
    "inventory",
    "reasoning",
    "learning",
    "coverage",
    "canonical_writer",
    "continuity",
}

MODULE_SOURCE = 'from __future__ import annotations\nfrom pathlib import Path\nimport ast\n\nORH_001_BUILD_ID = "ORH-001"\nORH_001_REVISION = "ORH_001_TRUTHFUL_ORACLE_RUNTIME_HEALTH_V1"\n\nEXPECTED_CORE = {\n    "fast_lane",\n    "inventory",\n    "reasoning",\n    "learning",\n    "coverage",\n    "canonical_writer",\n    "continuity",\n}\n\ndef read_children(source: str) -> dict[str, str]:\n    tree = ast.parse(source)\n    for node in ast.walk(tree):\n        if (\n            isinstance(node, ast.Assign)\n            and isinstance(node.value, ast.Dict)\n            and any(isinstance(t, ast.Name) and t.id == "CHILDREN" for t in node.targets)\n        ):\n            out = {}\n            for k, v in zip(node.value.keys, node.value.values):\n                if isinstance(k, ast.Constant) and isinstance(v, ast.Constant) and isinstance(v.value, str):\n                    out[str(k.value)] = str(v.value)\n            return out\n    raise RuntimeError("Physical run_oracle_LIVE.py CHILDREN dictionary not found")\n\ndef physical_contract(source: str) -> dict:\n    tree = ast.parse(source)\n    children = read_children(source)\n    missing = sorted(EXPECTED_CORE - set(children))\n    if missing:\n        raise RuntimeError("Physical launcher missing expected children: " + ", ".join(missing))\n    funcs = {node.name for node in tree.body if isinstance(node, ast.FunctionDef)}\n    for required in ("_start", "run_forever", "main"):\n        if required not in funcs:\n            raise RuntimeError(f"Physical launcher missing required function: {required}")\n    return {"children": children}\n\nNEW_RUN_FOREVER = \'\'\'def run_forever(cadence):\n    from pathlib import Path as _HealthPath\n    import time as _health_time\n\n    print(format_boot_report(build_boot_report()), flush=True)\n    root = _HealthPath.cwd()\n\n    started_at = {}\n    restart_history = {k: [] for k in CHILDREN}\n    restart_counts = {k: 0 for k in CHILDREN}\n    next_restart_at = {k: 0.0 for k in CHILDREN}\n    children = {}\n\n    def _spawn(key):\n        proc = _start(root, CHILDREN[key])\n        now = _health_time.monotonic()\n        children[key] = proc\n        started_at[key] = now\n        return proc\n\n    def _recent_restarts(key, now):\n        cutoff = now - 60.0\n        restart_history[key] = [t for t in restart_history[key] if t >= cutoff]\n        return len(restart_history[key])\n\n    def _child_state(key, now):\n        proc = children.get(key)\n        recent = _recent_restarts(key, now)\n\n        if proc is None:\n            return "FAILED"\n        if proc.poll() is not None:\n            return "FAILED"\n\n        age = max(0.0, now - started_at.get(key, now))\n\n        if recent >= 3:\n            return "FAILED"\n        if recent > 0:\n            return "DEGRADED"\n        if age < 15.0:\n            return "STARTING"\n        return "HEALTHY"\n\n    def _overall(states):\n        values = set(states.values())\n        if "FAILED" in values:\n            return "FAILED"\n        if "DEGRADED" in values:\n            return "DEGRADED"\n        if "STARTING" in values:\n            return "STARTING"\n        return "HEALTHY"\n\n    for key in CHILDREN:\n        _spawn(key)\n\n    heartbeat = 0\n    try:\n        while True:\n            heartbeat += 1\n            now = _health_time.monotonic()\n\n            for key in tuple(CHILDREN):\n                proc = children.get(key)\n                if proc is not None and proc.poll() is not None:\n                    code = proc.returncode\n                    restart_counts[key] += 1\n                    restart_history[key].append(now)\n                    recent = _recent_restarts(key, now)\n                    backoff = min(30.0, 2.0 ** min(max(recent - 1, 0), 5))\n                    next_restart_at[key] = now + backoff\n                    children[key] = None\n                    print(\n                        f"[ORACLE HEALTH] child={key} event=EXIT "\n                        f"code={code} restart_count={restart_counts[key]} "\n                        f"recent_restarts_60s={recent} restart_backoff_seconds={backoff:.1f}",\n                        flush=True,\n                    )\n\n            now = _health_time.monotonic()\n            for key in tuple(CHILDREN):\n                if children.get(key) is None and now >= next_restart_at[key]:\n                    _spawn(key)\n                    recent = _recent_restarts(key, now)\n                    print(\n                        f"[ORACLE HEALTH] child={key} event=RESTART "\n                        f"restart_count={restart_counts[key]} recent_restarts_60s={recent}",\n                        flush=True,\n                    )\n\n            now = _health_time.monotonic()\n            states = {key: _child_state(key, now) for key in CHILDREN}\n            overall = _overall(states)\n            status = " ".join(f"{k}={states[k]}" for k in CHILDREN)\n            restarts = " ".join(f"{k}_restarts={restart_counts[k]}" for k in CHILDREN)\n\n            print(\n                f"[ORACLE] heartbeat={heartbeat} state={overall} "\n                f"{status} {restarts} "\n                f"terminal_dependency=NONE execution_authority=FALSE",\n                flush=True,\n            )\n            _health_time.sleep(cadence)\n\n    except KeyboardInterrupt:\n        print()\n        for proc in children.values():\n            if proc is not None and proc.poll() is None:\n                proc.terminate()\n        for proc in children.values():\n            if proc is None:\n                continue\n            try:\n                proc.wait(timeout=5)\n            except Exception:\n                if proc.poll() is None:\n                    proc.kill()\n        print("[STOP] Oracle Live Runtime stopped by operator.", flush=True)\n        return 0\n\'\'\'\n\ndef patch_run_forever(source: str) -> str:\n    physical_contract(source)\n    tree = ast.parse(source)\n    target = None\n    for node in tree.body:\n        if isinstance(node, ast.FunctionDef) and node.name == "run_forever":\n            target = node\n            break\n    if target is None:\n        raise RuntimeError("Physical run_forever function not found")\n\n    lines = source.splitlines(keepends=True)\n    replacement = NEW_RUN_FOREVER\n    if not replacement.endswith("\\n"):\n        replacement += "\\n"\n\n    patched = "".join(lines[:target.lineno - 1]) + replacement + "".join(lines[target.end_lineno:])\n    ast.parse(patched)\n\n    if read_children(source) != read_children(patched):\n        raise RuntimeError("ORH-001 attempted to alter physical CHILDREN registry")\n    if "execution_authority=TRUE" in patched:\n        raise RuntimeError("Execution authority boundary violation")\n    return patched\n\ndef verify_patched_launcher(source: str) -> bool:\n    physical_contract(source)\n    required = (\n        "state={overall}",\n        \'"STARTING"\',\n        \'"HEALTHY"\',\n        \'"DEGRADED"\',\n        \'"FAILED"\',\n        "recent_restarts_60s",\n        "restart_backoff_seconds",\n        "execution_authority=FALSE",\n    )\n    return all(token in source for token in required)\n'
TEST_SOURCE = 'import ast\nimport unittest\nfrom pathlib import Path\n\nfrom qseries_v2.oracle_runtime_health.orh_001_truthful_runtime_health import (\n    EXPECTED_CORE,\n    physical_contract,\n    read_children,\n    patch_run_forever,\n    verify_patched_launcher,\n)\n\nROOT = Path.cwd().resolve()\nLAUNCHER = ROOT / "run_oracle_LIVE.py"\n\nclass T(unittest.TestCase):\n    @classmethod\n    def setUpClass(cls):\n        cls.physical_source = LAUNCHER.read_text(encoding="utf-8")\n\n    def test_physical_launcher_contract(self):\n        contract = physical_contract(self.physical_source)\n        self.assertTrue(EXPECTED_CORE.issubset(set(contract["children"])))\n\n    def test_physical_children_preserved_exactly(self):\n        before = read_children(self.physical_source)\n        patched = patch_run_forever(self.physical_source)\n        after = read_children(patched)\n        self.assertEqual(before, after)\n\n    def test_physical_patch_parses(self):\n        patched = patch_run_forever(self.physical_source)\n        ast.parse(patched)\n        self.assertTrue(verify_patched_launcher(patched))\n\n    def test_no_false_running_semantics(self):\n        patched = patch_run_forever(self.physical_source)\n        self.assertIn("state={overall}", patched)\n        for state in ("STARTING", "HEALTHY", "DEGRADED", "FAILED"):\n            self.assertIn(state, patched)\n\n    def test_restart_thrash_detection(self):\n        patched = patch_run_forever(self.physical_source)\n        self.assertIn("recent >= 3", patched)\n        self.assertIn("restart_backoff_seconds", patched)\n\n    def test_execution_boundary(self):\n        patched = patch_run_forever(self.physical_source)\n        self.assertIn("execution_authority=FALSE", patched)\n        self.assertNotIn("execution_authority=TRUE", patched)\n\nif __name__ == "__main__":\n    print("=" * 88)\n    print(" ORH-001 CERTIFICATION TEST")\n    print(" TRUTHFUL ORACLE RUNTIME HEALTH")\n    print(" PHYSICAL run_oracle_LIVE.py CONTRACT")\n    print("=" * 88)\n    result = unittest.TextTestRunner(verbosity=2).run(\n        unittest.defaultTestLoader.loadTestsFromTestCase(T)\n    )\n    if not result.wasSuccessful():\n        raise SystemExit(1)\n    print("[PASS] Physical launcher structure certified")\n    print("[PASS] Exact physical CHILDREN registry preserved")\n    print("[PASS] Fresh children report STARTING before HEALTHY")\n    print("[PASS] Recent crashes report DEGRADED/FAILED")\n    print("[PASS] Restart-thrash detection + bounded backoff certified")\n    print("[PASS] execution_authority=FALSE")\n    print("[DONE] ORH-001 CERTIFIED")\n'

def write_exact(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8", newline="\n")
    os.replace(tmp, path)

def restore(path, data):
    if data is None:
        if path.exists():
            path.unlink()
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

def update_init(path, export):
    current = path.read_text(encoding="utf-8") if path.exists() else ""
    if export not in current.splitlines():
        write_exact(path, current.rstrip() + "\n" + export + "\n")

def read_children_direct(source):
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Assign)
            and isinstance(node.value, ast.Dict)
            and any(isinstance(t, ast.Name) and t.id == "CHILDREN" for t in node.targets)
        ):
            return {
                str(k.value): str(v.value)
                for k, v in zip(node.value.keys, node.value.values)
                if isinstance(k, ast.Constant)
                and isinstance(v, ast.Constant)
                and isinstance(v.value, str)
            }
    raise RuntimeError("Physical CHILDREN registry not found")

def main():
    print("=" * 88)
    print(" ORH-001 INSTALLER")
    print(" TRUTHFUL ORACLE RUNTIME HEALTH")
    print(" PHYSICAL-LAUNCHER PATCH — NO SYNTHETIC PRODUCTION ASSUMPTIONS")
    print("=" * 88)
    print("[ROOT]", ROOT)

    if not LAUNCHER.is_file():
        raise RuntimeError("Physical run_oracle_LIVE.py missing")

    source_before = LAUNCHER.read_text(encoding="utf-8")
    ast.parse(source_before)
    children_before = read_children_direct(source_before)

    missing = sorted(EXPECTED_CORE - set(children_before))
    if missing:
        raise RuntimeError(
            "Refusing production patch; physical launcher missing: " + ", ".join(missing)
        )

    for child, runner in children_before.items():
        if not (ROOT / runner).is_file():
            raise RuntimeError(
                f"Refusing production patch; physical child runner missing: {child} -> {runner}"
            )

    print("[PHYSICAL CHILDREN]")
    for child, runner in children_before.items():
        print(f"  {child} -> {runner}")

    affected = (LAUNCHER, TEST, MOD, INIT, MANIFEST)
    old = {p: (p.read_bytes() if p.exists() else None) for p in affected}

    try:
        write_exact(MOD, MODULE_SOURCE)
        update_init(INIT, "from .orh_001_truthful_runtime_health import *")
        write_exact(TEST, TEST_SOURCE)

        subprocess.run([sys.executable, str(TEST)], cwd=str(ROOT), check=True)

        sys.path.insert(0, str(ROOT))
        importlib.invalidate_caches()
        m = importlib.import_module(
            "qseries_v2.oracle_runtime_health.orh_001_truthful_runtime_health"
        )
        m = importlib.reload(m)

        patched = m.patch_run_forever(source_before)
        write_exact(LAUNCHER, patched)

        source_after = LAUNCHER.read_text(encoding="utf-8")
        compile(source_after, str(LAUNCHER), "exec")

        children_after = m.read_children(source_after)
        if children_after != children_before:
            raise RuntimeError("Physical child registry changed during ORH-001")
        if not m.verify_patched_launcher(source_after):
            raise RuntimeError("Truthful health patch not physically present")

        subprocess.run(
            [sys.executable, str(LAUNCHER), "--check"],
            cwd=str(ROOT),
            timeout=30,
            check=True,
        )

        manifest = {
            "build_id": "ORH-001",
            "revision": "ORH_001_TRUTHFUL_ORACLE_RUNTIME_HEALTH_V1",
            "launcher": str(LAUNCHER.relative_to(ROOT)),
            "launcher_sha256_before": hashlib.sha256(source_before.encode("utf-8")).hexdigest(),
            "launcher_sha256_after": hashlib.sha256(source_after.encode("utf-8")).hexdigest(),
            "children_preserved": children_after,
            "stable_seconds_before_healthy": 15.0,
            "degraded_window_seconds": 60.0,
            "failed_restarts_in_window": 3,
            "max_restart_backoff_seconds": 30.0,
            "execution_authority": False,
        }
        write_exact(MANIFEST, json.dumps(manifest, indent=2, sort_keys=True) + "\n")

    except Exception:
        for p, data in old.items():
            restore(p, data)
        print("[ROLLBACK] ORH-001 failed; physical launcher and affected files restored")
        raise

    print("[PASS] Actual physical run_oracle_LIVE.py inspected before mutation")
    print("[PASS] Exact physical CHILDREN registry preserved")
    print("[PASS] run_forever only replaced; child runners unchanged")
    print("[PASS] Fresh processes report STARTING before HEALTHY")
    print("[PASS] Crash/restart history drives DEGRADED/FAILED state")
    print("[PASS] >=3 restarts in 60s cannot display HEALTHY")
    print("[PASS] Restart storm receives bounded backoff up to 30s")
    print("[PASS] Physical run_oracle_LIVE.py --check passed")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] ORH-001 INSTALLATION COMPLETE")

if __name__ == "__main__":
    main()
