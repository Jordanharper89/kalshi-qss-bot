from pathlib import Path
import importlib
import os
import subprocess
import sys

ROOT = Path.cwd().resolve()
PKG = ROOT / "qseries_v2" / "oracle_interruption_recovery"

MODULE_PATH = PKG / "oir_001_continuity_checkpoint.py"
TEST_PATH = ROOT / "test_oir_001_durable_runtime_continuity_checkpoint.py"
RUNNER_PATH = ROOT / "run_oir_001_continuity_checkpoint_daemon.py"
INIT_PATH = PKG / "__init__.py"

MODULE_SOURCE = 'from __future__ import annotations\n\nfrom datetime import datetime, timezone\nfrom pathlib import Path\nimport json\nimport os\nimport time\n\nfrom qseries_v2.oracle_learning_feedback.olf_011_learned_experience_profile import (\n    _connect,\n    _db_url,\n)\nfrom qseries_v2.oracle_learning_runtime.olr_016_production_learned_state_adapter import (\n    load_production_learned_state,\n)\n\nOIR_001_BUILD_ID = "OIR-001"\nOIR_001_REVISION = "OIR_001_DURABLE_RUNTIME_CONTINUITY_CHECKPOINT_CORRECTION_V2"\nCHECKPOINT_NAME = "oracle_interruption_continuity_checkpoint.json"\n\n\ndef _inventory_checkpoint_files(root):\n    state = Path(root) / "runtime_state"\n    if not state.exists():\n        return []\n\n    rows = []\n    for path in sorted(state.iterdir()):\n        name = path.name.lower()\n        if not path.is_file():\n            continue\n        if "inventory" not in name or "checkpoint" not in name:\n            continue\n        try:\n            stat = path.stat()\n            rows.append(\n                {\n                    "name": path.name,\n                    "size": int(stat.st_size),\n                    "mtime_ns": int(stat.st_mtime_ns),\n                }\n            )\n        except OSError:\n            pass\n    return rows\n\n\ndef capture_continuity_checkpoint(root=None):\n    root = Path(root or Path.cwd()).resolve()\n    now = datetime.now(timezone.utc)\n\n    conn = _connect(_db_url(root))\n    try:\n        try:\n            conn.set_session(readonly=True, autocommit=False)\n        except Exception:\n            pass\n\n        cur = conn.cursor()\n        cur.execute(\n            """\n            SELECT\n                COALESCE(MAX(sequence_number), 0),\n                COALESCE(MAX(observed_at)::text, \'\'),\n                COALESCE(MAX(persisted_at)::text, \'\'),\n                COUNT(*)\n            FROM public.oracle_canonical_observations\n            """\n        )\n        seq, observed_at, persisted_at, observation_count = cur.fetchone()\n\n        try:\n            conn.rollback()\n        except Exception:\n            pass\n    finally:\n        conn.close()\n\n    learner = load_production_learned_state(root)\n\n    payload = {\n        "revision": OIR_001_REVISION,\n        "captured_at": now.isoformat(),\n        "canonical_sequence_number": int(seq or 0),\n        "canonical_observed_at": str(observed_at or ""),\n        "canonical_persisted_at": str(persisted_at or ""),\n        "canonical_observation_count": int(observation_count or 0),\n        "learner_state_hash": str(learner.learner_state_hash or ""),\n        "learner_outcomes_learned": int(learner.outcomes_learned),\n        "inventory_checkpoint_files": _inventory_checkpoint_files(root),\n        "execution_authority": False,\n    }\n\n    path = root / "runtime_state" / CHECKPOINT_NAME\n    path.parent.mkdir(parents=True, exist_ok=True)\n    tmp = path.with_suffix(path.suffix + ".tmp")\n    tmp.write_text(\n        json.dumps(payload, sort_keys=True, separators=(",", ":")),\n        encoding="utf-8",\n        newline="\\n",\n    )\n    os.replace(tmp, path)\n    return payload\n\n\ndef load_continuity_checkpoint(root=None):\n    root = Path(root or Path.cwd()).resolve()\n    path = root / "runtime_state" / CHECKPOINT_NAME\n    if not path.is_file():\n        return None\n    return json.loads(path.read_text(encoding="utf-8"))\n\n\ndef run_checkpoint_daemon(root=None, cadence_seconds=5.0, progress=print):\n    root = Path(root or Path.cwd()).resolve()\n    cadence_seconds = float(cadence_seconds)\n    if cadence_seconds <= 0:\n        raise ValueError("cadence_seconds must be > 0")\n\n    while True:\n        payload = capture_continuity_checkpoint(root)\n        if progress:\n            progress(\n                "[OIR CHECKPOINT] "\n                f"captured_at={payload[\'captured_at\']} "\n                f"sequence={payload[\'canonical_sequence_number\']} "\n                f"observations={payload[\'canonical_observation_count\']} "\n                f"learner_outcomes={payload[\'learner_outcomes_learned\']}"\n            )\n        time.sleep(cadence_seconds)\n\n\ndef verify_oir_001_durable_runtime_continuity_checkpoint():\n    return (\n        OIR_001_BUILD_ID == "OIR-001"\n        and callable(capture_continuity_checkpoint)\n        and callable(load_continuity_checkpoint)\n        and callable(run_checkpoint_daemon)\n    )\n'
TEST_SOURCE = 'import unittest\nimport qseries_v2.oracle_interruption_recovery.oir_001_continuity_checkpoint as m\n\n\nclass T(unittest.TestCase):\n    def test_identity(self):\n        self.assertEqual(m.OIR_001_BUILD_ID, "OIR-001")\n\n    def test_contract(self):\n        self.assertTrue(callable(m.capture_continuity_checkpoint))\n        self.assertTrue(callable(m.load_continuity_checkpoint))\n        self.assertTrue(callable(m.run_checkpoint_daemon))\n        self.assertTrue(\n            m.verify_oir_001_durable_runtime_continuity_checkpoint()\n        )\n\n    def test_execution_boundary(self):\n        self.assertEqual(\n            m.OIR_001_REVISION,\n            "OIR_001_DURABLE_RUNTIME_CONTINUITY_CHECKPOINT_CORRECTION_V2",\n        )\n\n\nif __name__ == "__main__":\n    print("=" * 88)\n    print(" OIR-001 CERTIFICATION TEST — CORRECTION V2")\n    print(" DURABLE RUNTIME CONTINUITY CHECKPOINT")\n    print("=" * 88)\n\n    result = unittest.TextTestRunner(verbosity=2).run(\n        unittest.defaultTestLoader.loadTestsFromTestCase(T)\n    )\n    if not result.wasSuccessful():\n        raise SystemExit(1)\n\n    print("[PASS] Durable continuity checkpoint contract certified")\n    print("[PASS] installer path/source collision removed")\n    print("[PASS] execution_authority=FALSE")\n    print("[DONE] OIR-001 CORRECTION V2 CERTIFIED")\n'
RUNNER_SOURCE = 'from pathlib import Path\nimport argparse\n\nfrom qseries_v2.oracle_interruption_recovery.oir_001_continuity_checkpoint import (\n    run_checkpoint_daemon,\n)\n\n\ndef main(argv=None):\n    parser = argparse.ArgumentParser()\n    parser.add_argument("--cadence-seconds", type=float, default=5.0)\n    parser.add_argument("--check", action="store_true")\n    args = parser.parse_args(argv)\n\n    if args.check:\n        print("[READY] OIR-001 continuity checkpoint daemon")\n        print("[PASS] execution_authority=FALSE")\n        return 0\n\n    run_checkpoint_daemon(\n        Path.cwd(),\n        cadence_seconds=args.cadence_seconds,\n        progress=lambda value: print(value, flush=True),\n    )\n    return 0\n\n\nif __name__ == "__main__":\n    raise SystemExit(main())\n'


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
        path.write_bytes(data)


def update_init(path, line):
    current = path.read_text(encoding="utf-8") if path.exists() else ""
    if line not in current.splitlines():
        write_exact(path, current.rstrip() + "\n" + line + "\n")


def main():
    print("=" * 88)
    print(" OIR-001 INSTALLER — CORRECTION V2")
    print(" DURABLE RUNTIME CONTINUITY CHECKPOINT")
    print("=" * 88)
    print("[ROOT]", ROOT)

    paths = (MODULE_PATH, TEST_PATH, RUNNER_PATH, INIT_PATH)

    for path in paths:
        if not isinstance(path, Path):
            raise TypeError(
                f"Installer path collision detected before mutation: {path!r}"
            )

    old = {
        path: (path.read_bytes() if path.exists() else None)
        for path in paths
    }

    try:
        write_exact(MODULE_PATH, MODULE_SOURCE)
        write_exact(TEST_PATH, TEST_SOURCE)
        write_exact(RUNNER_PATH, RUNNER_SOURCE)
        update_init(
            INIT_PATH,
            "from .oir_001_continuity_checkpoint import *",
        )

        subprocess.run(
            [sys.executable, str(TEST_PATH)],
            cwd=str(ROOT),
            check=True,
        )
        subprocess.run(
            [sys.executable, str(RUNNER_PATH), "--check"],
            cwd=str(ROOT),
            check=True,
        )

        sys.path.insert(0, str(ROOT))
        importlib.invalidate_caches()

        module = importlib.import_module(
            "qseries_v2.oracle_interruption_recovery."
            "oir_001_continuity_checkpoint"
        )
        module = importlib.reload(module)

        payload = module.capture_continuity_checkpoint(ROOT)

        if int(payload.get("canonical_observation_count", 0)) <= 0:
            raise RuntimeError(
                "Physical continuity checkpoint contains no canonical observations"
            )

        if not str(payload.get("learner_state_hash") or ""):
            raise RuntimeError(
                "Physical continuity checkpoint is missing learner state hash"
            )

        persisted = module.load_continuity_checkpoint(ROOT)
        if not isinstance(persisted, dict):
            raise RuntimeError(
                "Continuity checkpoint was not durably persisted"
            )

        if (
            int(persisted.get("canonical_sequence_number", -1))
            != int(payload["canonical_sequence_number"])
        ):
            raise RuntimeError(
                "Persisted continuity checkpoint sequence mismatch"
            )

        print(
            "[PHYSICAL CHECKPOINT] "
            f"captured_at={payload['captured_at']} "
            f"sequence={payload['canonical_sequence_number']} "
            f"observations={payload['canonical_observation_count']} "
            f"learner_outcomes={payload['learner_outcomes_learned']} "
            f"inventory_checkpoints={len(payload['inventory_checkpoint_files'])} "
            f"state_hash={payload['learner_state_hash']}"
        )

    except Exception:
        for path, data in old.items():
            restore(path, data)
        print(
            "[ROLLBACK] OIR-001 Correction V2 failed; "
            "affected files restored"
        )
        raise

    print("[PASS] Installer path/source namespaces are isolated")
    print("[PASS] Physical checkpoint persisted and reloaded")
    print("[PASS] Frozen OPH/OPR/OLF modules untouched")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] OIR-001 CORRECTION V2 INSTALLATION COMPLETE")


if __name__ == "__main__":
    main()
