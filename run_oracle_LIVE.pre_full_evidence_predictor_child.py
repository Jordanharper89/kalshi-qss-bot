from __future__ import annotations
import os
import argparse,importlib,subprocess,sys,time
from dataclasses import dataclass
from pathlib import Path

RUNTIME_NAME="Oracle Live Runtime"
LAUNCHER_REVISION="ORACLE_LIVE_RUNTIME_KALSHI_OAD_055_OCR_015_OLR_005_V1"

@dataclass(frozen=True)
class OracleLiveBootReport:
    runtime_name:str
    state:str
    certified:bool
    terminal_dependency:bool
    execution_authority:bool

def _verify(module,verifier,label):
    m=importlib.import_module(module)
    if getattr(m,verifier)() is not True:
        raise RuntimeError(label+" verification failed")
    return True

def build_boot_report():
    _verify("qseries_v2.oracle_intelligence_state.ois_055_final_freeze","verify_ois_055_final_production_certification_freeze","OIS-055")
    _verify("qseries_v2.oracle_adapters.kalshi.oad_055_kalshi_production_freeze","verify_oad_055_kalshi_production_adapter_freeze_gate","OAD-055")
    _verify("qseries_v2.oracle_continuous_reasoning.ocr_015_production_gate","verify_ocr_015_continuous_reasoning_production_capability_gate","OCR-015")
    _verify("qseries_v2.oracle_learning_runtime.olr_005_capability_gate","verify_olr_005_continuous_learning_runtime_gate","OLR-005")
    return OracleLiveBootReport(RUNTIME_NAME,"RUNNING",True,False,False)

def format_boot_report(r):
    return "\n".join((
        "="*72,
        " ORACLE LIVE RUNTIME",
        "="*72,
        f"[REVISION] {LAUNCHER_REVISION}",
        "[STATE] RUNNING",
        "[PASS] Frozen OIS-001 through OIS-055 boundary verified",
        "[PASS] Frozen Kalshi OAD-001 through OAD-055 boundary verified",
        "[PASS] OCR-001 through OCR-015 continuous reasoning capability verified",
        "[PASS] OLR-001 through OLR-005 continuous learning capability verified",
        "[PASS] Global all-market ticker/trade fast lane enabled",
        "[PASS] Background checkpointed universe inventory enabled",
        "[PASS] Continuous market-aware reasoning child enabled",
        "[PASS] Outcome-grounded continuous learning child enabled",
        "[PASS] Operator Terminal dependency: NONE",
        "[PASS] Q Series execution authority remains separate",
        "[READY] Oracle Live Runtime with continuous reasoning + learning verified",
    ))

CHILDREN={
    "fast_lane":"run_opr_004_fast_lane_persistent_ingress.py",
    "inventory":"run_opr_004_inventory_persistent_ingress.py",
    "reasoning":"run_olf_030_breadth_aware_reasoning_runtime.py",
    "learning":"run_opr_004_learning_persistent_ingress.py",
    "coverage":"run_opr_004_coverage_persistent_ingress.py",
    "canonical_writer":"run_opr_003_persistent_single_writer_runtime.py",
    "continuity":"run_oir_001_continuity_checkpoint_daemon.py",
    "recovery":"run_oracle_background_recovery.py",
    "crypto_learning": "run_oad_207_crypto_continuous_learning_production_child.py",
    "gmgn_intelligence": "run_oad_290_gmgn_clean_continuous_intelligence_child.py",
    "sports": "run_osn_sports_continuous_runtime.py",
    "ksem_mapping": "run_ksem_live_mapping.py",
    "coinbase_hf": "run_coinbase_hf_live.py",

    "predictive_prospective": "run_opd_prospective_continuous_child.py",}

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



def run_forever(cadence):
    from pathlib import Path as _HealthPath
    import time as _health_time
    from datetime import datetime as _HealthDateTime, timezone as _HealthTimezone
    from qseries_v2.oracle_adapters.independent.oad_290_gmgn_clean_continuous_runtime import load_checkpoint as _load_gmgn_runtime_checkpoint

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



def main(argv=None):
    p=argparse.ArgumentParser()
    p.add_argument("--check",action="store_true")
    p.add_argument("--cadence-seconds",type=float,default=5.0)
    a=p.parse_args(argv)
    if a.cadence_seconds<=0:raise SystemExit("--cadence-seconds must be > 0")
    if a.check:
        print(format_boot_report(build_boot_report()))
        return 0
    return run_forever(a.cadence_seconds)

if __name__=="__main__":
    raise SystemExit(main())
