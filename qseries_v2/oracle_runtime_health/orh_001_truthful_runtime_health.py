from __future__ import annotations
from pathlib import Path
import ast

ORH_001_BUILD_ID = "ORH-001"
ORH_001_REVISION = "ORH_001_TRUTHFUL_ORACLE_RUNTIME_HEALTH_CORRECTION_V2"

EXPECTED_CORE = {
    "fast_lane",
    "inventory",
    "reasoning",
    "learning",
    "coverage",
    "canonical_writer",
    "continuity",
}

def read_children(source: str) -> dict[str, str]:
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Assign)
            and isinstance(node.value, ast.Dict)
            and any(isinstance(t, ast.Name) and t.id == "CHILDREN" for t in node.targets)
        ):
            out = {}
            for k, v in zip(node.value.keys, node.value.values):
                if isinstance(k, ast.Constant) and isinstance(v, ast.Constant) and isinstance(v.value, str):
                    out[str(k.value)] = str(v.value)
            return out
    raise RuntimeError("Physical run_oracle_LIVE.py CHILDREN dictionary not found")

def physical_contract(source: str) -> dict:
    tree = ast.parse(source)
    children = read_children(source)
    missing = sorted(EXPECTED_CORE - set(children))
    if missing:
        raise RuntimeError("Physical launcher missing expected children: " + ", ".join(missing))
    funcs = {node.name for node in tree.body if isinstance(node, ast.FunctionDef)}
    for required in ("_start", "run_forever", "main"):
        if required not in funcs:
            raise RuntimeError(f"Physical launcher missing required function: {required}")
    return {"children": children}

NEW_RUN_FOREVER = '''def run_forever(cadence):
    from pathlib import Path as _HealthPath
    import time as _health_time

    print(format_boot_report(build_boot_report()), flush=True)
    root = _HealthPath.cwd()

    started_at = {}
    restart_history = {k: [] for k in CHILDREN}
    restart_counts = {k: 0 for k in CHILDREN}
    next_restart_at = {k: 0.0 for k in CHILDREN}
    children = {}

    def _spawn(key):
        proc = _start(root, CHILDREN[key])
        now = _health_time.monotonic()
        children[key] = proc
        started_at[key] = now
        return proc

    def _recent_restarts(key, now):
        cutoff = now - 60.0
        restart_history[key] = [t for t in restart_history[key] if t >= cutoff]
        return len(restart_history[key])

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

def patch_run_forever(source: str) -> str:
    physical_contract(source)
    tree = ast.parse(source)
    target = None
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == "run_forever":
            target = node
            break
    if target is None:
        raise RuntimeError("Physical run_forever function not found")

    lines = source.splitlines(keepends=True)
    replacement = NEW_RUN_FOREVER
    if not replacement.endswith("\n"):
        replacement += "\n"

    patched = "".join(lines[:target.lineno - 1]) + replacement + "".join(lines[target.end_lineno:])
    ast.parse(patched)

    if read_children(source) != read_children(patched):
        raise RuntimeError("ORH-001 attempted to alter physical CHILDREN registry")
    if "execution_authority=TRUE" in patched:
        raise RuntimeError("Execution authority boundary violation")
    return patched

def verify_patched_launcher(source: str) -> bool:
    physical_contract(source)
    required = (
        "state={overall}",
        '"STARTING"',
        '"HEALTHY"',
        '"DEGRADED"',
        '"FAILED"',
        "recent_restarts_60s",
        "restart_backoff_seconds",
        "execution_authority=FALSE",
    )
    return all(token in source for token in required)
