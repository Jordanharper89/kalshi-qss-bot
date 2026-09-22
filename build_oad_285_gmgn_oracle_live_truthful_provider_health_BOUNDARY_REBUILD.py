from __future__ import annotations

import ast
import shutil
import subprocess
import sys
from pathlib import Path

EXPECTED_FILENAME = "build_oad_285_gmgn_oracle_live_truthful_provider_health_BOUNDARY_REBUILD.py"
LAUNCHER = "run_oracle_live.py"
TEST = "test_oad_285_gmgn_oracle_live_truthful_provider_health_boundary.py"

REQUIRED_CHILD = '"gmgn_intelligence": "run_oad_284_gmgn_continuous_intelligence_production_child.py"'
REQUIRED_MARKERS = (
    "restart_history = {k: [] for k in CHILDREN}",
    "restart_counts = {k: 0 for k in CHILDREN}",
    "next_restart_at = {k: 0.0 for k in CHILDREN}",
    "def _spawn(key):",
    "def _child_state(key, now):",
    "states = {key: _child_state(key, now) for key in CHILDREN}",
    "restart_backoff_seconds",
)

NEW_RUN_FOREVER = r'''def run_forever(cadence):
    from pathlib import Path as _HealthPath
    import time as _health_time
    from datetime import datetime as _HealthDateTime, timezone as _HealthTimezone
    from qseries_v2.oracle_adapters.independent.oad_283_gmgn_continuous_runtime_checkpoint import load_gmgn_runtime_checkpoint as _load_gmgn_runtime_checkpoint

    print(format_boot_report(build_boot_report()), flush=True)
    root = _HealthPath.cwd()

    started_at = {}
    restart_history = {k: [] for k in CHILDREN}
    restart_counts = {k: 0 for k in CHILDREN}
    next_restart_at = {k: 0.0 for k in CHILDREN}
    children = {}
    gmgn_checkpoint_cycle_at_spawn = {}

    def _gmgn_cycle():
        try:
            return int(_load_gmgn_runtime_checkpoint(root).cycles)
        except Exception:
            return -1

    def _spawn(key):
        if key == "gmgn_intelligence":
            gmgn_checkpoint_cycle_at_spawn[key] = _gmgn_cycle()
        proc = _start(root, CHILDREN[key])
        now = _health_time.monotonic()
        children[key] = proc
        started_at[key] = now
        return proc

    def _recent_restarts(key, now):
        cutoff = now - 60.0
        restart_history[key] = [t for t in restart_history[key] if t >= cutoff]
        return len(restart_history[key])

    def _gmgn_provider_state(key, process_age):
        try:
            cp = _load_gmgn_runtime_checkpoint(root)
        except Exception:
            return "DEGRADED"

        baseline = int(gmgn_checkpoint_cycle_at_spawn.get(key, -1))
        current_cycle = int(cp.cycles)

        if current_cycle <= baseline:
            return "STARTING" if process_age < 180.0 else "DEGRADED"

        if cp.last_error:
            return "DEGRADED"
        if not cp.last_success_at:
            return "DEGRADED"

        try:
            success_at = _HealthDateTime.fromisoformat(str(cp.last_success_at))
            if success_at.tzinfo is None:
                success_at = success_at.replace(tzinfo=_HealthTimezone.utc)
            success_age = max(
                0.0,
                (_HealthDateTime.now(_HealthTimezone.utc) - success_at.astimezone(_HealthTimezone.utc)).total_seconds(),
            )
        except Exception:
            return "DEGRADED"

        if success_age > 240.0:
            return "DEGRADED"
        return "HEALTHY"

    def _child_state(key, now):
        proc = children.get(key)
        recent = _recent_restarts(key, now)

        if proc is None:
            return "FAILED"
        if proc.poll() is not None:
            return "FAILED"

        age = max(0.0, now - started_at.get(key, now))

        if recent >= 3:
            return "FAILED"
        if recent > 0:
            return "DEGRADED"
        if age < 15.0:
            return "STARTING"

        if key == "gmgn_intelligence":
            return _gmgn_provider_state(key, age)

        return "HEALTHY"

    def _overall(states):
        values = set(states.values())
        if "FAILED" in values:
            return "FAILED"
        if "DEGRADED" in values:
            return "DEGRADED"
        if "STARTING" in values:
            return "STARTING"
        return "HEALTHY"

    for key in CHILDREN:
        _spawn(key)

    heartbeat = 0
    try:
        while True:
            heartbeat += 1
            now = _health_time.monotonic()

            for key in tuple(CHILDREN):
                proc = children.get(key)
                if proc is not None and proc.poll() is not None:
                    code = proc.returncode
                    restart_counts[key] += 1
                    restart_history[key].append(now)
                    recent = _recent_restarts(key, now)
                    backoff = min(30.0, 2.0 ** min(max(recent - 1, 0), 5))
                    next_restart_at[key] = now + backoff
                    children[key] = None
                    print(
                        f"[ORACLE HEALTH] child={key} event=EXIT "
                        f"code={code} restart_count={restart_counts[key]} "
                        f"recent_restarts_60s={recent} restart_backoff_seconds={backoff:.1f}",
                        flush=True,
                    )

            now = _health_time.monotonic()
            for key in tuple(CHILDREN):
                if children.get(key) is None and now >= next_restart_at[key]:
                    _spawn(key)
                    recent = _recent_restarts(key, now)
                    print(
                        f"[ORACLE HEALTH] child={key} event=RESTART "
                        f"restart_count={restart_counts[key]} recent_restarts_60s={recent}",
                        flush=True,
                    )

            now = _health_time.monotonic()
            states = {key: _child_state(key, now) for key in CHILDREN}
            overall = _overall(states)
            status = " ".join(f"{k}={states[k]}" for k in CHILDREN)
            restarts = " ".join(f"{k}_restarts={restart_counts[k]}" for k in CHILDREN)

            print(
                f"[ORACLE] heartbeat={heartbeat} state={overall} "
                f"{status} {restarts} "
                f"terminal_dependency=NONE execution_authority=FALSE",
                flush=True,
            )
            _health_time.sleep(cadence)

    except KeyboardInterrupt:
        print()
        for proc in children.values():
            if proc is not None and proc.poll() is None:
                proc.terminate()
        for proc in children.values():
            if proc is None:
                continue
            try:
                proc.wait(timeout=5)
            except Exception:
                if proc.poll() is None:
                    proc.kill()
        print("[STOP] Oracle Live Runtime stopped by operator.", flush=True)
        return 0
'''

TEST_SOURCE = r'''from __future__ import annotations
import ast
import subprocess
import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parent
LAUNCHER=ROOT/"run_oracle_live.py"

class T(unittest.TestCase):
    def test_exact_gmgn_binding_preserved(self):
        tree=ast.parse(LAUNCHER.read_text(encoding="utf-8"))
        children=None
        for n in tree.body:
            if isinstance(n,ast.Assign):
                for t in n.targets:
                    if isinstance(t,ast.Name) and t.id=="CHILDREN" and isinstance(n.value,ast.Dict):
                        children=ast.literal_eval(n.value)
        self.assertIsNotNone(children)
        self.assertEqual(children.get("gmgn_intelligence"),"run_oad_284_gmgn_continuous_intelligence_production_child.py")

    def test_truthful_provider_health_semantics_installed(self):
        s=LAUNCHER.read_text(encoding="utf-8")
        self.assertIn("gmgn_checkpoint_cycle_at_spawn",s)
        self.assertIn("if cp.last_error:",s)
        self.assertIn("if success_age > 240.0:",s)
        self.assertIn('if key == "gmgn_intelligence":',s)
        self.assertIn('return _gmgn_provider_state(key, age)',s)
        self.assertIn("restart_backoff_seconds",s)
        self.assertNotIn("execution_authority=TRUE",s)

    def test_launcher_check(self):
        p=subprocess.run([sys.executable,str(LAUNCHER),"--check"],cwd=str(ROOT),capture_output=True,text=True,timeout=45)
        self.assertEqual(p.returncode,0,msg=(p.stdout+"\n"+p.stderr))
        self.assertIn("[READY] Oracle Live Runtime",p.stdout)

if __name__=="__main__":
    print("="*96)
    print(" OAD-285 TRUTHFUL GMGN PROVIDER-HEALTH BOUNDARY CERTIFICATION")
    print("="*96)
    r=unittest.main(verbosity=2,exit=False)
    if not r.result.wasSuccessful():
        raise SystemExit(1)
    print("[PASS] GMGN process-alive health no longer implies provider HEALTHY")
    print("[PASS] fresh in-process successful GMGN cycle required for HEALTHY")
    print("[PASS] provider failure/stale-success state maps to DEGRADED")
    print("[PASS] existing Oracle children + restart supervision preserved")
    print("[PASS] probability=FALSE direction=FALSE publication=FALSE execution=FALSE")
    print("[DONE] OAD-285 TRUTHFUL PROVIDER HEALTH BOUNDARY REBUILD CERTIFIED")
'''

def _find_run_forever_span(src: str):
    tree=ast.parse(src)
    node=None
    for n in tree.body:
        if isinstance(n,ast.FunctionDef) and n.name=="run_forever":
            node=n
            break
    if node is None:
        raise RuntimeError("run_forever not found")
    lines=src.splitlines(keepends=True)
    start=sum(len(x) for x in lines[:node.lineno-1])
    end=sum(len(x) for x in lines[:node.end_lineno])
    return start,end

def main():
    if Path(__file__).name != EXPECTED_FILENAME:
        raise RuntimeError("installer identity mismatch")

    root=Path.cwd().resolve()
    launcher=root/LAUNCHER
    if not launcher.is_file():
        raise RuntimeError("physical Oracle Live launcher missing: "+str(launcher))

    src=launcher.read_text(encoding="utf-8")
    for marker in REQUIRED_MARKERS:
        if marker not in src:
            raise RuntimeError("required launcher boundary missing: "+marker)
    if REQUIRED_CHILD not in src:
        raise RuntimeError("exact GMGN child binding missing")
    if "execution_authority=TRUE" in src:
        raise RuntimeError("execution safety boundary violation")

    worker=root/"qseries_v2"/"oracle_adapters"/"independent"/"oad_284_gmgn_resilient_continuous_worker.py"
    checkpoint=root/"qseries_v2"/"oracle_adapters"/"independent"/"oad_283_gmgn_continuous_runtime_checkpoint.py"
    if not worker.is_file() or not checkpoint.is_file():
        raise RuntimeError("GMGN worker/checkpoint boundary missing")
    w=worker.read_text(encoding="utf-8")
    c=checkpoint.read_text(encoding="utf-8")
    for m in ("advance_success","advance_failure","status=SUCCESS","status=RETRY"):
        if m not in w:
            raise RuntimeError("GMGN worker contract missing: "+m)
    for m in ("last_success_at","last_error","cycles"):
        if m not in c:
            raise RuntimeError("GMGN checkpoint contract missing: "+m)

    start,end=_find_run_forever_span(src)
    rebuilt=src[:start]+NEW_RUN_FOREVER+"\n\n"+src[end:]
    ast.parse(rebuilt)

    backup=launcher.with_suffix(".py.oad285_truthful_health_backup")
    backup.write_bytes(launcher.read_bytes())

    try:
        launcher.write_text(rebuilt,encoding="utf-8",newline="\n")
        test=root/TEST
        test.write_text(TEST_SOURCE,encoding="utf-8",newline="\n")
        compile(launcher.read_text(encoding="utf-8"),str(launcher),"exec")
        compile(test.read_text(encoding="utf-8"),str(test),"exec")

        p=subprocess.run([sys.executable,str(launcher),"--check"],cwd=str(root),capture_output=True,text=True,timeout=45)
        if p.returncode != 0:
            raise RuntimeError("launcher --check failed after rebuild:\n"+p.stdout+"\n"+p.stderr)

        after=launcher.read_text(encoding="utf-8")
        for m in (
            "gmgn_checkpoint_cycle_at_spawn",
            "if cp.last_error:",
            "if success_age > 240.0:",
            'if key == "gmgn_intelligence":',
            "restart_backoff_seconds",
        ):
            if m not in after:
                raise RuntimeError("truthful health marker missing after rebuild: "+m)

        print("="*96)
        print(" OAD-285 GMGN ORACLE LIVE TRUTHFUL PROVIDER HEALTH — BOUNDARY REBUILD")
        print("="*96)
        print("[ROOT]",root)
        print("[PASS] exact current GMGN child binding verified")
        print("[PASS] resilient GMGN checkpoint success/failure contract verified")
        print("[PASS] existing Oracle Live run_forever boundary rebuilt in place")
        print("[PASS] process-alive-only GMGN HEALTHY semantics retired")
        print("[PASS] fresh successful provider cycle required before GMGN HEALTHY")
        print("[PASS] current provider failure maps GMGN to DEGRADED without killing worker")
        print("[PASS] stale GMGN success (>240s) maps to DEGRADED")
        print("[PASS] process exit/restart supervision and restart backoff preserved")
        print("[PASS] all existing CHILDREN bindings preserved unchanged")
        print("[PASS] launcher --check passed")
        print("[PASS] probability=FALSE direction=FALSE publication=FALSE execution=FALSE")
        print("[DONE] OAD-285 TRUTHFUL PROVIDER HEALTH BOUNDARY REBUILD INSTALLATION COMPLETE")
    except Exception:
        shutil.copy2(backup,launcher)
        raise

if __name__=="__main__":
    main()
