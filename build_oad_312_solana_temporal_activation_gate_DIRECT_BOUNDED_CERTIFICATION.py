
from __future__ import annotations
import ast, hashlib, os, textwrap
from pathlib import Path

EXPECTED = "build_oad_312_solana_temporal_activation_gate_DIRECT_BOUNDED_CERTIFICATION.py"
MODULE = "oad_312_solana_continuous_temporal_history_activation_gate.py"
TEST = "test_oad_312_solana_continuous_temporal_history_activation_gate.py"

DEPS = {
    "qseries_v2/oracle_adapters/independent/oad_272_solana_continuous_observation_policy.py":
        ("build_solana_continuous_observation_policy",),
    "qseries_v2/oracle_adapters/independent/oad_273_solana_pinned_pool_live_snapshot_persistence.py":
        ("select_live_solana_token", "persist_pinned_solana_pool_snapshot", "exact_postgresql_readback"),
    "qseries_v2/oracle_adapters/independent/oad_274_solana_multi_horizon_condition_windows.py":
        ("read_pinned_pool_history", "build_multi_horizon_solana_states"),
    "qseries_v2/oracle_adapters/independent/oad_275_solana_continuous_observation_resilient_worker.py":
        ("run_solana_continuous_cycle",),
    "qseries_v2/oracle_adapters/independent/oad_276_solana_continuous_observation_production_runner.py":
        ("evaluate_solana_continuous_runner",),
}

MODULE_SOURCE = r"""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import time

from .oad_272_solana_continuous_observation_policy import build_solana_continuous_observation_policy
from .oad_273_solana_pinned_pool_live_snapshot_persistence import select_live_solana_token
from .oad_275_solana_continuous_observation_resilient_worker import run_solana_continuous_cycle
from .oad_276_solana_continuous_observation_production_runner import evaluate_solana_continuous_runner

READ_ONLY=True
PROBABILITY_ENABLED=False
DIRECTION_ENABLED=False
PUBLICATION_ALLOWED=False
EXECUTION_AUTHORITY=False

@dataclass(frozen=True, slots=True)
class SolanaTemporalActivationResult:
    runner_admitted: bool
    token_address: str
    successful_cycles: int
    history_records: int
    windows: tuple
    ready_windows: tuple
    temporal_state: str
    execution_authority: bool=False

def activate_and_verify_temporal_history(
    root=None,
    cycles=13,
    acquisition_seconds=5.0,
    acquisition_timeout_seconds=20.0,
    persistence_timeout_seconds=30.0,
    sleep_fn=time.sleep,
    progress=print,
):
    root=Path(root or Path.cwd()).resolve()
    admission=evaluate_solana_continuous_runner(root)
    if not admission.admitted:
        raise RuntimeError("certified OAD-276 Solana continuous runner not admitted")

    cycles=max(13,int(cycles))
    policy=build_solana_continuous_observation_policy(
        tick_seconds=1.0,
        acquisition_seconds=float(acquisition_seconds),
        history_limit=512,
        windows_seconds=(5,15,30,60),
        acquisition_timeout_seconds=float(acquisition_timeout_seconds),
        persistence_timeout_seconds=float(persistence_timeout_seconds),
    )

    token=select_live_solana_token(policy.acquisition_timeout_seconds)
    progress("[PIN] token_address="+token)

    last=None
    for n in range(1,cycles+1):
        started=time.monotonic()
        progress(f"[CERT] cycle={n}/{cycles} starting token={token}")
        try:
            last=run_solana_continuous_cycle(
                root=root,
                policy=policy,
                cycle=n,
                token_address=token,
            )
        except Exception as exc:
            progress(f"[FAIL] cycle={n} type={type(exc).__name__} message={exc}")
            raise RuntimeError(
                f"OAD-312 physical certification failed at cycle {n}; "
                f"{type(exc).__name__}: {exc}"
            ) from exc

        compact=tuple((w.window_seconds,w.records,w.state) for w in last.windows)
        progress(
            f"[CERT] cycle={n}/{cycles} history={last.history_records} "
            f"windows={compact} execution_authority=FALSE"
        )

        if n < cycles:
            elapsed=time.monotonic()-started
            delay=max(0.0,policy.acquisition_seconds-elapsed)
            if delay:
                sleep_fn(delay)

    if last is None:
        raise RuntimeError("OAD-312 certification produced no successful cycle")

    compact=tuple((w.window_seconds,w.records,w.state) for w in last.windows)
    ready=tuple(w.window_seconds for w in last.windows if w.state=="WINDOW_READY")
    required={5,15,30,60}
    state=(
        "TEMPORAL_5_15_30_60_READY"
        if required.issubset(set(ready))
        else "TEMPORAL_DEPTH_STILL_ACCUMULATING"
    )

    return SolanaTemporalActivationResult(
        runner_admitted=True,
        token_address=token,
        successful_cycles=cycles,
        history_records=last.history_records,
        windows=compact,
        ready_windows=ready,
        temporal_state=state,
        execution_authority=False,
    )
"""

TEST_SOURCE = r"""
import unittest
from qseries_v2.oracle_adapters.independent.oad_312_solana_continuous_temporal_history_activation_gate import *

class T(unittest.TestCase):
    def test_physical_activation(self):
        x=activate_and_verify_temporal_history()
        print("[PHYSICAL] runner_admitted=",x.runner_admitted)
        print("[PHYSICAL] token=",x.token_address)
        print("[PHYSICAL] successful_cycles=",x.successful_cycles)
        print("[PHYSICAL] history_records=",x.history_records)
        print("[PHYSICAL] windows=",x.windows)
        print("[PHYSICAL] ready_windows=",x.ready_windows)
        print("[PHYSICAL] temporal_state=",x.temporal_state)

        self.assertTrue(x.runner_admitted)
        self.assertTrue(x.token_address)
        self.assertEqual(x.successful_cycles,13)
        self.assertGreaterEqual(x.history_records,2)
        self.assertIn(5,x.ready_windows)
        self.assertIn(15,x.ready_windows)
        self.assertIn(30,x.ready_windows)
        self.assertIn(60,x.ready_windows)
        self.assertEqual(x.temporal_state,"TEMPORAL_5_15_30_60_READY")
        self.assertFalse(x.execution_authority)

if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(T)
    )
    if not r.wasSuccessful():
        raise SystemExit(1)
    print("[PASS] OAD-312 direct bounded Solana temporal-history activation certified")
    print("[PASS] 13 pinned physical acquisitions completed with live cycle output")
    print("[PASS] durable 5/15/30/60-second windows all WINDOW_READY")
    print("[PASS] OAD-272→276 production path preserved unchanged")
    print("[PASS] probability=FALSE direction=FALSE publication=FALSE execution=FALSE")
"""

def root():
    for b in (Path.cwd().resolve(), Path(__file__).resolve().parent):
        for p in (b,*b.parents):
            if (p/"qseries_v2").is_dir():
                return p
    raise RuntimeError("Q Series repository root not found")

def write_checked(path,source):
    source=textwrap.dedent(source).lstrip()
    ast.parse(source,filename=str(path))
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(source,encoding="utf-8",newline="\n")
    os.replace(tmp,path)

def main():
    if Path(__file__).name != EXPECTED:
        raise RuntimeError("installer filename identity mismatch")
    r=root()
    pkg=r/"qseries_v2"/"oracle_adapters"/"independent"
    m=pkg/MODULE
    t=r/TEST
    init=pkg/"__init__.py"

    print("="*120)
    print(" OAD-312 SOLANA TEMPORAL ACTIVATION GATE — DIRECT BOUNDED CERTIFICATION INSTALLER")
    print("="*120)
    print("[ROOT]",r)

    for rel,markers in DEPS.items():
        p=r/rel
        if not p.is_file():
            raise RuntimeError("dependency missing: "+rel)
        s=p.read_text(encoding="utf-8")
        ast.parse(s,filename=str(p))
        for marker in markers:
            if marker not in s:
                raise RuntimeError("exact dependency marker missing: "+rel+" -> "+marker)
        print("[PASS] exact dependency verified:",rel)

    protected=[]
    for rel in (
        "qseries_v2/oracle_production_hardening/oph_023_postgresql_single_writer_production_freeze.py",
        "qseries_v2/oracle_adapters/kalshi/oad_055_kalshi_production_freeze.py",
        "qseries_v2/oracle_adapters/independent/oad_272_solana_continuous_observation_policy.py",
        "qseries_v2/oracle_adapters/independent/oad_273_solana_pinned_pool_live_snapshot_persistence.py",
        "qseries_v2/oracle_adapters/independent/oad_274_solana_multi_horizon_condition_windows.py",
        "qseries_v2/oracle_adapters/independent/oad_275_solana_continuous_observation_resilient_worker.py",
        "qseries_v2/oracle_adapters/independent/oad_276_solana_continuous_observation_production_runner.py",
    ):
        p=r/rel
        if not p.is_file():
            raise RuntimeError("protected dependency missing: "+rel)
        protected.append((p,hashlib.sha256(p.read_bytes()).hexdigest()))

    old={p:(p.read_bytes() if p.exists() else None) for p in (m,t,init)}
    try:
        write_checked(m,MODULE_SOURCE)
        write_checked(t,TEST_SOURCE)

        lines=init.read_text(encoding="utf-8").splitlines() if init.exists() else []
        exp="from ."+m.stem+" import *"
        if exp not in lines:
            lines.append(exp)
        write_checked(init,"\n".join(x for x in lines if x.strip())+"\n")

        for p,h in protected:
            if hashlib.sha256(p.read_bytes()).hexdigest()!=h:
                raise RuntimeError("protected/frozen dependency changed: "+p.name)

        print("[PASS] bad subprocess/captured-output certification wrapper retired")
        print("[PASS] OAD-312 now invokes certified OAD-275 cycle boundary directly")
        print("[PASS] live progress emitted for every physical acquisition")
        print("[PASS] certification is fail-fast on first physical acquisition/persistence error")
        print("[PASS] 13 successful pinned acquisitions required")
        print("[PASS] 5/15/30/60-second WINDOW_READY state required")
        print("[PASS] OAD-272→276 unchanged")
        print("[PASS] OPH-023/Kalshi OAD-055 unchanged")
        print("[PASS] probability=FALSE direction=FALSE publication=FALSE execution=FALSE")
        print("[DONE] OAD-312 DIRECT BOUNDED CERTIFICATION INSTALLED")
    except Exception:
        for p,data in old.items():
            if data is None:
                if p.exists(): p.unlink()
            else:
                p.write_bytes(data)
        print("[ROLLBACK] OAD-312 files restored")
        raise

if __name__=="__main__":
    main()
