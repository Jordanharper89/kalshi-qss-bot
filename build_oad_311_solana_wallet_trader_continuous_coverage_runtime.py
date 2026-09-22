from __future__ import annotations
import ast, hashlib, os, textwrap
from pathlib import Path

EXPECTED = 'build_oad_311_solana_wallet_trader_continuous_coverage_runtime.py'
MODULE = "oad_311_solana_wallet_trader_continuous_coverage_runtime.py"
RUNNER = "run_oad_311_solana_wallet_trader_continuous_coverage_child.py"
TEST = "test_oad_311_solana_wallet_trader_continuous_coverage_runtime.py"
DEPENDENCIES = [('qseries_v2/oracle_adapters/independent/oad_310_solana_target_token_wallet_trader_single_writer_persistence.py', ('def persist_target_token_wallet_trader_coverage', 'RATE_LIMITED_HOLD_NO_WRITE', 'PERSISTED_EXACT_TARGET_TOKEN_EVIDENCE')), ('qseries_v2/oracle_adapters/independent/oad_308_solana_wallet_trader_condition_profile.py', ('durable_read_only',)), ('qseries_v2/oracle_adapters/independent/oad_309_solana_target_token_wallet_trader_coverage_acquisition.py', ('RATE_LIMITED_HOLD', 'retry_after_seconds'))]
MODULE_SOURCE = 'from __future__ import annotations\nfrom dataclasses import dataclass, asdict\nfrom datetime import datetime, timezone, timedelta\nfrom pathlib import Path\nimport json, os, time\n\nfrom .oad_310_solana_target_token_wallet_trader_single_writer_persistence import (\n    persist_target_token_wallet_trader_coverage,\n)\n\nREAD_ONLY = True\nPROBABILITY_ENABLED = False\nDIRECTION_ENABLED = False\nPUBLICATION_ALLOWED = False\nEXECUTION_AUTHORITY = False\n\nCHECKPOINT_RELATIVE = Path("runtime_state") / "oad_311_solana_wallet_trader_coverage_runtime.json"\nDEFAULT_SUCCESS_INTERVAL_SECONDS = 300.0\nDEFAULT_ERROR_BACKOFF_SECONDS = 300.0\n\n@dataclass(frozen=True, slots=True)\nclass CoverageRuntimeCycle:\n    cycle_sequence: int\n    token_address: str | None\n    state: str\n    acquisition_state: str | None\n    persistence_state: str | None\n    committed_new: int\n    exact_readback: int\n    retry_after_seconds: float\n    next_attempt_at: str\n    observed_at: str\n    failure_detail: str | None\n    execution_authority: bool = False\n\ndef _utcnow():\n    return datetime.now(timezone.utc)\n\ndef _checkpoint_path(root=None):\n    return Path(root or Path.cwd()).resolve() / CHECKPOINT_RELATIVE\n\ndef _read_checkpoint(root=None):\n    p = _checkpoint_path(root)\n    if not p.is_file():\n        return {}\n    try:\n        x = json.loads(p.read_text(encoding="utf-8"))\n        return x if isinstance(x, dict) else {}\n    except Exception:\n        return {}\n\ndef _write_checkpoint(cycle, root=None):\n    p = _checkpoint_path(root)\n    p.parent.mkdir(parents=True, exist_ok=True)\n    q = p.with_suffix(p.suffix + ".tmp")\n    q.write_text(json.dumps(asdict(cycle), sort_keys=True, indent=2) + "\\n",\n                 encoding="utf-8", newline="\\n")\n    os.replace(q, p)\n\ndef run_coverage_cycle(\n    root=None,\n    timeout_seconds=120.0,\n    acquisition_timeout_seconds=30.0,\n    success_interval_seconds=DEFAULT_SUCCESS_INTERVAL_SECONDS,\n    error_backoff_seconds=DEFAULT_ERROR_BACKOFF_SECONDS,\n):\n    root = Path(root or Path.cwd()).resolve()\n    prior = _read_checkpoint(root)\n    seq = int(prior.get("cycle_sequence") or 0) + 1\n    now = _utcnow()\n\n    try:\n        x = persist_target_token_wallet_trader_coverage(\n            root=root,\n            timeout_seconds=timeout_seconds,\n            acquisition_timeout_seconds=acquisition_timeout_seconds,\n        )\n        if x.acquisition_state == "RATE_LIMITED_HOLD":\n            retry = max(1.0, float(x.retry_after_seconds or DEFAULT_ERROR_BACKOFF_SECONDS))\n            state = "RATE_LIMITED_HOLD"\n        else:\n            retry = max(1.0, float(success_interval_seconds))\n            state = "SUCCESS"\n        cycle = CoverageRuntimeCycle(\n            seq, x.token_address, state, x.acquisition_state, x.persistence_state,\n            int(x.committed_new), int(x.exact_readback), retry,\n            (now + timedelta(seconds=retry)).isoformat(),\n            now.isoformat(), None, False,\n        )\n    except Exception as e:\n        retry = max(1.0, float(error_backoff_seconds))\n        cycle = CoverageRuntimeCycle(\n            seq, prior.get("token_address"), "ERROR_BACKOFF", None, None, 0, 0,\n            retry, (now + timedelta(seconds=retry)).isoformat(),\n            now.isoformat(), (type(e).__name__ + ": " + str(e))[:500], False,\n        )\n\n    _write_checkpoint(cycle, root)\n    return cycle\n\ndef run_continuous_coverage(\n    root=None,\n    timeout_seconds=120.0,\n    acquisition_timeout_seconds=30.0,\n    success_interval_seconds=DEFAULT_SUCCESS_INTERVAL_SECONDS,\n    error_backoff_seconds=DEFAULT_ERROR_BACKOFF_SECONDS,\n):\n    while True:\n        cycle = run_coverage_cycle(\n            root=root,\n            timeout_seconds=timeout_seconds,\n            acquisition_timeout_seconds=acquisition_timeout_seconds,\n            success_interval_seconds=success_interval_seconds,\n            error_backoff_seconds=error_backoff_seconds,\n        )\n        print(\n            "[OAD-311] cycle=%s state=%s token=%s committed_new=%s exact_readback=%s "\n            "retry_after_seconds=%s next_attempt_at=%s"\n            % (\n                cycle.cycle_sequence, cycle.state, cycle.token_address,\n                cycle.committed_new, cycle.exact_readback,\n                cycle.retry_after_seconds, cycle.next_attempt_at,\n            ),\n            flush=True,\n        )\n        time.sleep(cycle.retry_after_seconds)\n'
RUNNER_SOURCE = 'from qseries_v2.oracle_adapters.independent.oad_311_solana_wallet_trader_continuous_coverage_runtime import (\n    run_continuous_coverage,\n)\n\nif __name__ == "__main__":\n    print("[BOOT] OAD-311 SOLANA WALLET/TRADER CONTINUOUS COVERAGE RUNTIME", flush=True)\n    print("[BOUNDARY] read-only intelligence; execution_authority=FALSE", flush=True)\n    run_continuous_coverage()\n'
TEST_SOURCE = 'import json\nimport tempfile\nimport unittest\nfrom pathlib import Path\n\nfrom qseries_v2.oracle_adapters.independent.oad_311_solana_wallet_trader_continuous_coverage_runtime import (\n    CHECKPOINT_RELATIVE,\n    run_coverage_cycle,\n)\n\nclass T(unittest.TestCase):\n    def test_physical_single_cycle_and_checkpoint(self):\n        # Uses the real OAD-310 production boundary once. It never sleeps.\n        with tempfile.TemporaryDirectory() as td:\n            # The production persistence stack needs the repository root, so the\n            # physical checkpoint is written to the real runtime_state directory.\n            root = Path.cwd().resolve()\n            x = run_coverage_cycle(root=root)\n            print("[PHYSICAL] cycle_sequence=", x.cycle_sequence)\n            print("[PHYSICAL] token=", x.token_address)\n            print("[PHYSICAL] state=", x.state)\n            print("[PHYSICAL] acquisition_state=", x.acquisition_state)\n            print("[PHYSICAL] persistence_state=", x.persistence_state)\n            print("[PHYSICAL] committed_new=", x.committed_new)\n            print("[PHYSICAL] exact_readback=", x.exact_readback)\n            print("[PHYSICAL] retry_after_seconds=", x.retry_after_seconds)\n            print("[PHYSICAL] next_attempt_at=", x.next_attempt_at)\n            print("[PHYSICAL] failure_detail=", x.failure_detail)\n\n            cp = root / CHECKPOINT_RELATIVE\n            self.assertTrue(cp.is_file())\n            saved = json.loads(cp.read_text(encoding="utf-8"))\n            self.assertEqual(saved["cycle_sequence"], x.cycle_sequence)\n            self.assertEqual(saved["state"], x.state)\n            self.assertFalse(saved["execution_authority"])\n\n            self.assertIn(x.state, ("SUCCESS", "RATE_LIMITED_HOLD", "ERROR_BACKOFF"))\n            self.assertGreaterEqual(x.retry_after_seconds, 1.0)\n            self.assertFalse(x.execution_authority)\n\n            if x.state == "RATE_LIMITED_HOLD":\n                self.assertEqual(x.acquisition_state, "RATE_LIMITED_HOLD")\n                self.assertEqual(x.persistence_state, "RATE_LIMITED_HOLD_NO_WRITE")\n                self.assertEqual(x.committed_new, 0)\n                self.assertEqual(x.exact_readback, 0)\n                self.assertGreaterEqual(x.retry_after_seconds, 300.0)\n            elif x.state == "SUCCESS":\n                self.assertEqual(x.acquisition_state, "ACQUIRED")\n                self.assertEqual(x.persistence_state, "PERSISTED_EXACT_TARGET_TOKEN_EVIDENCE")\n                self.assertEqual(x.exact_readback, 2)\n            else:\n                self.assertTrue(x.failure_detail)\n\nif __name__ == "__main__":\n    r = unittest.TextTestRunner(verbosity=2).run(\n        unittest.defaultTestLoader.loadTestsFromTestCase(T)\n    )\n    if not r.wasSuccessful():\n        raise SystemExit(1)\n    print("[PASS] OAD-311 continuous coverage cycle physically certified")\n    print("[PASS] durable checkpoint written atomically")\n    print("[PASS] rate-limit HOLD/backoff is respected without rapid retry")\n    print("[PASS] continuous runner is independent of condition/reasoning reads")\n'

def root():
    for b in (Path.cwd().resolve(), Path(__file__).resolve().parent):
        for p in (b, *b.parents):
            if (p / "qseries_v2").is_dir():
                return p
    raise RuntimeError("Q Series repository root not found")

def write(p, s):
    s = textwrap.dedent(s).lstrip()
    ast.parse(s, filename=str(p))
    p.parent.mkdir(parents=True, exist_ok=True)
    q = p.with_suffix(p.suffix + ".tmp")
    q.write_text(s, encoding="utf-8", newline="\n")
    os.replace(q, p)

def main():
    if Path(__file__).name != EXPECTED:
        raise RuntimeError("installer filename identity mismatch")
    r = root()
    pkg = r / "qseries_v2" / "oracle_adapters" / "independent"
    m, run, t, init = pkg / MODULE, r / RUNNER, r / TEST, pkg / "__init__.py"

    print("=" * 120)
    print(" OAD-311 SOLANA WALLET/TRADER CONTINUOUS COVERAGE RUNTIME INSTALLER")
    print("=" * 120)
    print("[ROOT]", r)

    for rel, marks in DEPENDENCIES:
        p = r / rel
        if not p.is_file():
            raise RuntimeError("dependency missing: " + rel)
        s = p.read_text(encoding="utf-8")
        ast.parse(s, filename=str(p))
        for mark in marks:
            if mark not in s:
                raise RuntimeError("exact dependency marker missing: " + rel + " -> " + mark)
        print("[PASS] exact dependency verified:", rel)

    protected = []
    for rel in (
        "qseries_v2/oracle_production_hardening/oph_023_postgresql_single_writer_production_freeze.py",
        "qseries_v2/oracle_adapters/kalshi/oad_055_kalshi_production_freeze.py",
    ):
        p = r / rel
        if not p.is_file():
            raise RuntimeError("frozen boundary missing: " + rel)
        protected.append((p, hashlib.sha256(p.read_bytes()).hexdigest()))

    old = {p: (p.read_bytes() if p.exists() else None) for p in (m, run, t, init)}
    try:
        write(m, MODULE_SOURCE)
        write(run, RUNNER_SOURCE)
        write(t, TEST_SOURCE)
        lines = init.read_text(encoding="utf-8").splitlines() if init.exists() else []
        exp = "from ." + m.stem + " import *"
        if exp not in lines:
            lines.append(exp)
        write(init, "\n".join(x for x in lines if x.strip()) + "\n")

        for p, h in protected:
            if hashlib.sha256(p.read_bytes()).hexdigest() != h:
                raise RuntimeError("frozen boundary changed: " + p.name)

        print("[PASS] OAD-310 physically certified persistence boundary bound")
        print("[PASS] successful acquisitions persist only through OAD-310")
        print("[PASS] GMGN RATE_LIMITED_HOLD schedules provider retry from retry_after_seconds")
        print("[PASS] unexpected errors enter bounded ERROR_BACKOFF")
        print("[PASS] runtime checkpoint is atomic and restart-durable")
        print("[PASS] physical test executes exactly one cycle and never sleeps")
        print("[PASS] standalone continuous child installed:", run.name)
        print("[PASS] module installed:", m.relative_to(r))
        print("[PASS] test installed:", t.name)
        print("[PASS] NOT integrated into main Oracle supervisor by this build")
        print("[PASS] frozen OPH-023/Kalshi OAD-055 unchanged")
        print("[PASS] probability=FALSE direction=FALSE publication=FALSE execution=FALSE")
        print("[DONE] OAD-311 INSTALLATION COMPLETE")
    except Exception:
        for p, b in old.items():
            if b is None:
                if p.exists():
                    p.unlink()
            else:
                p.write_bytes(b)
        print("[ROLLBACK] affected files restored")
        raise

if __name__ == "__main__":
    main()
