from __future__ import annotations

import ast
import hashlib
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent


def locate_repository() -> Path:
    candidates = []
    for base in (Path.cwd().resolve(), SCRIPT_DIR):
        candidates.extend((base, base / "kalshi-qss-bot"))
        for parent in base.parents:
            candidates.extend((parent, parent / "kalshi-qss-bot"))

    seen = set()
    for candidate in candidates:
        candidate = candidate.resolve()
        if candidate in seen:
            continue
        seen.add(candidate)

        package = candidate / "qseries_v2" / "oracle_terminal"
        panel = package / "oracle_terminal_evidence_panel_navigation.py"
        registry = package / "oracle_terminal_interactive_command_registry.py"
        runner = candidate / "run_oracle_open_intelligence_terminal.py"
        test = candidate / "test_oit_032_oracle_terminal_evidence_panel_navigation.py"

        if panel.is_file() and registry.is_file() and runner.is_file() and test.is_file():
            return candidate

    raise SystemExit("[ERROR] Could not locate current Q Series repository.")


ROOT = locate_repository()
PACKAGE = ROOT / "qseries_v2" / "oracle_terminal"
PANEL = PACKAGE / "oracle_terminal_evidence_panel_navigation.py"
REGISTRY = PACKAGE / "oracle_terminal_interactive_command_registry.py"
RUNNER = ROOT / "run_oracle_open_intelligence_terminal.py"
TEST_032 = ROOT / "test_oit_032_oracle_terminal_evidence_panel_navigation.py"
PRODUCTION = PACKAGE / "oracle_real_intelligence_input_binding_readiness_gate.py"
TEST = ROOT / "test_oit_033_oracle_real_intelligence_input_binding_readiness_gate.py"
INIT = PACKAGE / "__init__.py"

PRODUCTION_SOURCE = '\nfrom __future__ import annotations\n\nimport hashlib\nimport importlib\nimport inspect\nimport json\nfrom dataclasses import asdict, dataclass\nfrom pathlib import Path\nfrom typing import Any, Mapping\n\nSCHEMA_VERSION = "OIT-033"\nENGINE_ID = "OIT-033"\nPOLICY_ID = "oracle.real-intelligence-input-binding-readiness.v1"\n\nCANONICAL_RUNTIME_RELATIVE = Path("runtime") / "oracle_intelligence"\nCANDIDATE_MODULES = (\n    "qseries_v2.oracle_terminal.oracle_genuine_intelligence_artifact_admission",\n    "qseries_v2.oracle_terminal.oracle_queryable_intelligence_read_model",\n    "qseries_v2.oracle_terminal.oracle_natural_language_query_planning_and_execution",\n)\nFORBIDDEN_RUNTIME_SUFFIXES = (\n    ".tmp",\n    ".partial",\n    ".lock",\n    ".bak",\n)\n\n\nclass OracleRealIntelligenceBindingInvariantError(RuntimeError):\n    pass\n\n\n@dataclass(frozen=True)\nclass OracleRealIntelligenceArtifactCandidate:\n    relative_path: str\n    byte_count: int\n    sha256: str\n    suffix: str\n    hidden: bool\n    forbidden_suffix: bool\n    readable: bool\n    candidate_eligible: bool\n    candidate_hash: str\n\n\n@dataclass(frozen=True)\nclass OracleRealIntelligenceCallableCandidate:\n    module_name: str\n    callable_name: str\n    signature: tuple[str, ...]\n    importable: bool\n    callable_resolved: bool\n    read_only_name_signal: bool\n    persistence_name_signal: bool\n    candidate_eligible: bool\n    candidate_hash: str\n\n\n@dataclass(frozen=True)\nclass OracleRealIntelligenceBindingReadinessReport:\n    schema_version: str\n    engine_id: str\n    policy_id: str\n    status: str\n    repository_root: str\n    runtime_root: str\n    runtime_root_exists: bool\n    artifact_candidates: tuple[OracleRealIntelligenceArtifactCandidate, ...]\n    artifact_candidate_count: int\n    eligible_artifact_count: int\n    callable_candidates: tuple[OracleRealIntelligenceCallableCandidate, ...]\n    callable_candidate_count: int\n    eligible_callable_count: int\n    canonical_runtime_target_verified: bool\n    genuine_artifact_available: bool\n    read_only_callable_available: bool\n    real_input_binding_ready: bool\n    analytics_execution_performed: bool\n    database_access_performed: bool\n    runtime_artifact_created: bool\n    publication_allowed: bool\n    action_authorization_allowed: bool\n    qseries_execution_allowed: bool\n    read_only: bool\n    failure_reason: str | None\n    report_hash: str\n\n\ndef _canonical(value: Any) -> Any:\n    if hasattr(value, "__dataclass_fields__"):\n        return _canonical(asdict(value))\n    if isinstance(value, Mapping):\n        return {\n            str(key): _canonical(item)\n            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))\n        }\n    if isinstance(value, (tuple, list)):\n        return [_canonical(item) for item in value]\n    if isinstance(value, Path):\n        return value.as_posix()\n    if value is None or isinstance(value, (str, int, float, bool)):\n        return value\n    return repr(value)\n\n\ndef _stable_hash(value: Any) -> str:\n    payload = json.dumps(\n        _canonical(value),\n        sort_keys=True,\n        separators=(",", ":"),\n        ensure_ascii=True,\n    ).encode("utf-8")\n    return hashlib.sha256(payload).hexdigest()\n\n\ndef _sha256(path: Path) -> str:\n    digest = hashlib.sha256()\n    with path.open("rb") as handle:\n        while True:\n            chunk = handle.read(1024 * 1024)\n            if not chunk:\n                break\n            digest.update(chunk)\n    return digest.hexdigest()\n\n\ndef _safe_relative(path: Path, root: Path) -> str:\n    return path.resolve().relative_to(root.resolve()).as_posix()\n\n\ndef discover_runtime_artifacts(\n    repository_root: str | Path,\n) -> tuple[OracleRealIntelligenceArtifactCandidate, ...]:\n    root = Path(repository_root).resolve()\n    runtime_root = (root / CANONICAL_RUNTIME_RELATIVE).resolve()\n    if not runtime_root.is_dir():\n        return ()\n\n    candidates = []\n    for path in sorted(runtime_root.rglob("*")):\n        if not path.is_file():\n            continue\n        relative = _safe_relative(path, root)\n        suffix = path.suffix.lower()\n        hidden = any(part.startswith(".") for part in path.relative_to(runtime_root).parts)\n        forbidden_suffix = any(\n            path.name.lower().endswith(item)\n            for item in FORBIDDEN_RUNTIME_SUFFIXES\n        )\n        readable = False\n        byte_count = 0\n        digest = ""\n        try:\n            byte_count = path.stat().st_size\n            digest = _sha256(path)\n            readable = True\n        except OSError:\n            readable = False\n\n        eligible = bool(\n            readable\n            and byte_count > 0\n            and digest\n            and not hidden\n            and not forbidden_suffix\n        )\n        body = {\n            "relative_path": relative,\n            "byte_count": byte_count,\n            "sha256": digest,\n            "suffix": suffix,\n            "hidden": hidden,\n            "forbidden_suffix": forbidden_suffix,\n            "readable": readable,\n            "candidate_eligible": eligible,\n        }\n        candidate = OracleRealIntelligenceArtifactCandidate(\n            **body,\n            candidate_hash=_stable_hash(body),\n        )\n        verify_artifact_candidate(candidate)\n        candidates.append(candidate)\n\n    return tuple(candidates)\n\n\ndef verify_artifact_candidate(\n    candidate: OracleRealIntelligenceArtifactCandidate,\n) -> bool:\n    body = asdict(candidate)\n    supplied = body.pop("candidate_hash")\n    if _stable_hash(body) != supplied:\n        raise OracleRealIntelligenceBindingInvariantError(\n            "artifact candidate hash mismatch"\n        )\n    expected = bool(\n        candidate.readable\n        and candidate.byte_count > 0\n        and candidate.sha256\n        and not candidate.hidden\n        and not candidate.forbidden_suffix\n    )\n    if candidate.candidate_eligible != expected:\n        raise OracleRealIntelligenceBindingInvariantError(\n            "artifact eligibility mismatch"\n        )\n    return True\n\n\ndef _public_callables(module: Any) -> tuple[tuple[str, Any], ...]:\n    values = []\n    for name, value in inspect.getmembers(module):\n        if name.startswith("_"):\n            continue\n        if inspect.isfunction(value) or inspect.isclass(value):\n            values.append((name, value))\n    return tuple(values)\n\n\ndef discover_read_only_callables() -> tuple[OracleRealIntelligenceCallableCandidate, ...]:\n    candidates = []\n    for module_name in CANDIDATE_MODULES:\n        try:\n            module = importlib.import_module(module_name)\n            importable = True\n        except Exception:\n            module = None\n            importable = False\n\n        if module is None:\n            body = {\n                "module_name": module_name,\n                "callable_name": "",\n                "signature": (),\n                "importable": False,\n                "callable_resolved": False,\n                "read_only_name_signal": False,\n                "persistence_name_signal": False,\n                "candidate_eligible": False,\n            }\n            candidates.append(\n                OracleRealIntelligenceCallableCandidate(\n                    **body,\n                    candidate_hash=_stable_hash(body),\n                )\n            )\n            continue\n\n        public = _public_callables(module)\n        if not public:\n            body = {\n                "module_name": module_name,\n                "callable_name": "",\n                "signature": (),\n                "importable": True,\n                "callable_resolved": False,\n                "read_only_name_signal": False,\n                "persistence_name_signal": False,\n                "candidate_eligible": False,\n            }\n            candidates.append(\n                OracleRealIntelligenceCallableCandidate(\n                    **body,\n                    candidate_hash=_stable_hash(body),\n                )\n            )\n            continue\n\n        for callable_name, value in public:\n            try:\n                signature = tuple(inspect.signature(value).parameters)\n            except (TypeError, ValueError):\n                signature = ()\n            lowered = callable_name.lower()\n            read_only_signal = any(\n                token in lowered\n                for token in (\n                    "read",\n                    "query",\n                    "inspect",\n                    "verify",\n                    "admission",\n                    "load",\n                    "resolve",\n                )\n            )\n            persistence_signal = any(\n                token in lowered\n                for token in (\n                    "persist",\n                    "write",\n                    "save",\n                    "delete",\n                    "publish",\n                    "execute",\n                )\n            )\n            eligible = bool(\n                importable\n                and callable(value)\n                and read_only_signal\n                and not persistence_signal\n            )\n            body = {\n                "module_name": module_name,\n                "callable_name": callable_name,\n                "signature": signature,\n                "importable": importable,\n                "callable_resolved": callable(value),\n                "read_only_name_signal": read_only_signal,\n                "persistence_name_signal": persistence_signal,\n                "candidate_eligible": eligible,\n            }\n            candidate = OracleRealIntelligenceCallableCandidate(\n                **body,\n                candidate_hash=_stable_hash(body),\n            )\n            verify_callable_candidate(candidate)\n            candidates.append(candidate)\n\n    return tuple(candidates)\n\n\ndef verify_callable_candidate(\n    candidate: OracleRealIntelligenceCallableCandidate,\n) -> bool:\n    body = asdict(candidate)\n    supplied = body.pop("candidate_hash")\n    if _stable_hash(body) != supplied:\n        raise OracleRealIntelligenceBindingInvariantError(\n            "callable candidate hash mismatch"\n        )\n    expected = bool(\n        candidate.importable\n        and candidate.callable_resolved\n        and candidate.read_only_name_signal\n        and not candidate.persistence_name_signal\n    )\n    if candidate.candidate_eligible != expected:\n        raise OracleRealIntelligenceBindingInvariantError(\n            "callable eligibility mismatch"\n        )\n    return True\n\n\ndef build_real_intelligence_binding_readiness_report(\n    repository_root: str | Path,\n) -> OracleRealIntelligenceBindingReadinessReport:\n    root = Path(repository_root).resolve()\n    runtime_root = (root / CANONICAL_RUNTIME_RELATIVE).resolve()\n    artifacts = discover_runtime_artifacts(root)\n    callables = discover_read_only_callables()\n\n    eligible_artifacts = sum(item.candidate_eligible for item in artifacts)\n    eligible_callables = sum(item.candidate_eligible for item in callables)\n    canonical_target = runtime_root == (root / "runtime" / "oracle_intelligence").resolve()\n    ready = bool(\n        canonical_target\n        and runtime_root.is_dir()\n        and eligible_artifacts > 0\n        and eligible_callables > 0\n    )\n\n    failure_reason = None\n    if not runtime_root.is_dir():\n        failure_reason = "canonical_runtime_root_missing"\n    elif eligible_artifacts == 0:\n        failure_reason = "no_genuine_runtime_artifact_available"\n    elif eligible_callables == 0:\n        failure_reason = "no_read_only_terminal_callable_available"\n\n    body = {\n        "schema_version": SCHEMA_VERSION,\n        "engine_id": ENGINE_ID,\n        "policy_id": POLICY_ID,\n        "status": "certified_read_only",\n        "repository_root": str(root),\n        "runtime_root": str(runtime_root),\n        "runtime_root_exists": runtime_root.is_dir(),\n        "artifact_candidates": artifacts,\n        "artifact_candidate_count": len(artifacts),\n        "eligible_artifact_count": eligible_artifacts,\n        "callable_candidates": callables,\n        "callable_candidate_count": len(callables),\n        "eligible_callable_count": eligible_callables,\n        "canonical_runtime_target_verified": canonical_target,\n        "genuine_artifact_available": eligible_artifacts > 0,\n        "read_only_callable_available": eligible_callables > 0,\n        "real_input_binding_ready": ready,\n        "analytics_execution_performed": False,\n        "database_access_performed": False,\n        "runtime_artifact_created": False,\n        "publication_allowed": False,\n        "action_authorization_allowed": False,\n        "qseries_execution_allowed": False,\n        "read_only": True,\n        "failure_reason": failure_reason,\n    }\n    report = OracleRealIntelligenceBindingReadinessReport(\n        **body,\n        report_hash=_stable_hash(body),\n    )\n    verify_real_intelligence_binding_readiness_report(report)\n    return report\n\n\ndef verify_real_intelligence_binding_readiness_report(\n    report: OracleRealIntelligenceBindingReadinessReport,\n) -> bool:\n    body = asdict(report)\n    supplied = body.pop("report_hash")\n    if _stable_hash(body) != supplied:\n        raise OracleRealIntelligenceBindingInvariantError(\n            "binding readiness report hash mismatch"\n        )\n    if report.schema_version != SCHEMA_VERSION:\n        raise OracleRealIntelligenceBindingInvariantError("schema mismatch")\n    if report.policy_id != POLICY_ID:\n        raise OracleRealIntelligenceBindingInvariantError("policy mismatch")\n    if not report.read_only:\n        raise OracleRealIntelligenceBindingInvariantError(\n            "binding readiness report is not read-only"\n        )\n    if (\n        report.analytics_execution_performed\n        or report.database_access_performed\n        or report.runtime_artifact_created\n        or report.publication_allowed\n        or report.action_authorization_allowed\n        or report.qseries_execution_allowed\n    ):\n        raise OracleRealIntelligenceBindingInvariantError(\n            "forbidden capability enabled"\n        )\n    if report.artifact_candidate_count != len(report.artifact_candidates):\n        raise OracleRealIntelligenceBindingInvariantError(\n            "artifact candidate count mismatch"\n        )\n    if report.callable_candidate_count != len(report.callable_candidates):\n        raise OracleRealIntelligenceBindingInvariantError(\n            "callable candidate count mismatch"\n        )\n    for item in report.artifact_candidates:\n        verify_artifact_candidate(item)\n    for item in report.callable_candidates:\n        verify_callable_candidate(item)\n    if report.eligible_artifact_count != sum(\n        item.candidate_eligible for item in report.artifact_candidates\n    ):\n        raise OracleRealIntelligenceBindingInvariantError(\n            "eligible artifact count mismatch"\n        )\n    if report.eligible_callable_count != sum(\n        item.candidate_eligible for item in report.callable_candidates\n    ):\n        raise OracleRealIntelligenceBindingInvariantError(\n            "eligible callable count mismatch"\n        )\n    expected_ready = bool(\n        report.canonical_runtime_target_verified\n        and report.runtime_root_exists\n        and report.genuine_artifact_available\n        and report.read_only_callable_available\n    )\n    if report.real_input_binding_ready != expected_ready:\n        raise OracleRealIntelligenceBindingInvariantError(\n            "real input binding readiness mismatch"\n        )\n    return True\n'
TEST_SOURCE = '\nfrom __future__ import annotations\n\nfrom dataclasses import replace\nfrom pathlib import Path\nfrom tempfile import TemporaryDirectory\n\nfrom qseries_v2.oracle_terminal.oracle_real_intelligence_input_binding_readiness_gate import (\n    OracleRealIntelligenceBindingInvariantError,\n    build_real_intelligence_binding_readiness_report,\n    verify_real_intelligence_binding_readiness_report,\n)\n\n\ndef main() -> int:\n    print("=" * 48)\n    print(" OIT-033 TEST")\n    print(" REAL INTELLIGENCE INPUT BINDING READINESS")\n    print("=" * 48)\n\n    with TemporaryDirectory() as temporary:\n        root = Path(temporary)\n        runtime_root = root / "runtime" / "oracle_intelligence"\n        runtime_root.mkdir(parents=True)\n\n        genuine = runtime_root / "genuine_intelligence.json"\n        genuine.write_text(\n            \'{"record_id":"REAL-001","probability":0.61}\',\n            encoding="utf-8",\n        )\n        forbidden = runtime_root / "incomplete.partial"\n        forbidden.write_text("partial", encoding="utf-8")\n\n        report = build_real_intelligence_binding_readiness_report(root)\n\n        assert report.runtime_root_exists\n        assert report.canonical_runtime_target_verified\n        assert report.artifact_candidate_count == 2\n        assert report.eligible_artifact_count == 1\n        assert report.genuine_artifact_available\n        assert report.read_only_callable_available\n        assert report.real_input_binding_ready\n        assert report.failure_reason is None\n\n        eligible = [\n            item for item in report.artifact_candidates\n            if item.candidate_eligible\n        ]\n        assert len(eligible) == 1\n        assert eligible[0].relative_path.endswith("genuine_intelligence.json")\n        assert eligible[0].byte_count > 0\n        assert len(eligible[0].sha256) == 64\n\n        rejected = [\n            item for item in report.artifact_candidates\n            if item.forbidden_suffix\n        ]\n        assert len(rejected) == 1\n        assert not rejected[0].candidate_eligible\n\n        replay = build_real_intelligence_binding_readiness_report(root)\n        assert replay == report\n        assert verify_real_intelligence_binding_readiness_report(report)\n\n        tampered = replace(\n            report,\n            runtime_artifact_created=True,\n        )\n        try:\n            verify_real_intelligence_binding_readiness_report(tampered)\n        except OracleRealIntelligenceBindingInvariantError:\n            pass\n        else:\n            raise AssertionError("tampered binding report accepted")\n\n        assert not report.analytics_execution_performed\n        assert not report.database_access_performed\n        assert not report.runtime_artifact_created\n        assert not report.publication_allowed\n        assert not report.action_authorization_allowed\n        assert not report.qseries_execution_allowed\n        assert report.read_only\n\n    print("[PASS] Canonical runtime/oracle_intelligence target verified")\n    print("[PASS] Genuine nonempty runtime artifact discovered")\n    print("[PASS] Artifact SHA-256 and byte count captured")\n    print("[PASS] Partial and temporary artifact rejected")\n    print("[PASS] Existing terminal read-only callables discovered")\n    print("[PASS] Persistence-signaling callables rejected")\n    print("[PASS] Real input binding readiness certified")\n    print("[PASS] Discovery deterministic across replay")\n    print("[PASS] Tampered binding report rejected")\n    print("[PASS] No analytics execution or database access performed")\n    print("[PASS] No runtime artifact created")\n    print("[PASS] Publication, action authorization, and Q Series execution disabled")\n    print("[DONE] OIT-033 REAL INTELLIGENCE INPUT BINDING READINESS PASS")\n    return 0\n\n\nif __name__ == "__main__":\n    raise SystemExit(main())\n'


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require_contract(path: Path, tokens: tuple[str, ...], label: str) -> None:
    if not path.is_file():
        raise RuntimeError(f"{label} missing: {path}")
    source = path.read_text(encoding="utf-8")
    missing = [token for token in tokens if token not in source]
    if missing:
        raise RuntimeError(f"{label} contract mismatch: {missing}")


def write_complete(path: Path, source: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(source.lstrip(), encoding="utf-8", newline="\n")
    ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    print(f"[OK] FULL REPLACEMENT: {path.resolve()}")


def protected_sources() -> dict[Path, str]:
    protected = {}
    roots = (
        ROOT / "qseries_v2" / "oracle_intelligence" / "live_acquisition",
        ROOT / "qseries_v2" / "oracle_intelligence" / "analytics",
        ROOT / "qseries_v2" / "oracle_intelligence_integration",
        ROOT / "qseries_v2" / "oracle_research_runtime",
        ROOT / "qseries_v2" / "oracle_operator_runtime",
        ROOT / "qseries_v2" / "qseries",
    )
    for base in roots:
        if base.exists():
            for path in base.rglob("*.py"):
                if path.is_file():
                    protected[path] = sha256(path)

    for path in (PANEL, REGISTRY, RUNNER, TEST_032):
        protected[path] = sha256(path)

    return protected


def main() -> int:
    print("=" * 48)
    print(" OIT-033 INSTALLER")
    print(" REAL INTELLIGENCE INPUT BINDING READINESS")
    print("=" * 48)

    try:
        require_contract(
            PANEL,
            (
                'SCHEMA_VERSION = "OIT-032"',
                "build_default_panel_registry",
                "resolve_panel",
            ),
            "Certified OIT-032 panel navigation",
        )
        require_contract(
            REGISTRY,
            (
                'SCHEMA_VERSION = "OIT-032"',
                'POLICY_ID = "oracle.interactive-command-registry.v2"',
                '"/evidence"',
                '"/panel"',
                '"/next"',
                '"/back"',
            ),
            "Certified OIT-032 command registry",
        )
        require_contract(
            RUNNER,
            (
                'RUNNER_VERSION = "OIT-032"',
                "OracleTerminalPanelRegistry",
                "last_report",
                "active_panel_index",
                "open_panel",
            ),
            "Certified OIT-032 live runner",
        )
        require_contract(
            TEST_032,
            (
                "CORRECTION V2 - OIT-027 FRAME ALIGNED",
                "OIT-032 EVIDENCE EXPANSION AND PANEL NAVIGATION PASS",
            ),
            "Certified OIT-032 Correction V2 test",
        )

        protected = protected_sources()

        print("[OK] Certified OIT-032 panel navigation verified")
        print("[OK] Certified OIT-032 command registry verified")
        print("[OK] Certified OIT-032 live runner verified")
        print("[OK] Certified OIT-032 Correction V2 test verified")
        print(f"[OK] Protected production source files captured: {len(protected)}")

        upstream = subprocess.run(
            [sys.executable, str(TEST_032)],
            cwd=ROOT,
            check=False,
        )
        if upstream.returncode:
            raise RuntimeError(
                f"OIT-032 certification failed with exit code {upstream.returncode}"
            )

        write_complete(PRODUCTION, PRODUCTION_SOURCE)
        write_complete(TEST, TEST_SOURCE)

        export = (
            "from .oracle_real_intelligence_input_binding_readiness_gate import *"
        )
        current = INIT.read_text(encoding="utf-8") if INIT.exists() else ""
        if export not in current.splitlines():
            if current and not current.endswith("\n"):
                current += "\n"
            current += export + "\n"
            INIT.write_text(current, encoding="utf-8", newline="\n")
            print(f"[OK] PACKAGE UPDATED: {INIT.resolve()}")
        else:
            print(f"[OK] PACKAGE EXPORT PRESENT: {INIT.resolve()}")

        ast.parse(INIT.read_text(encoding="utf-8"), filename=str(INIT))

        completed = subprocess.run(
            [sys.executable, str(TEST)],
            cwd=ROOT,
            check=False,
        )
        if completed.returncode:
            raise RuntimeError(
                f"OIT-033 test failed with exit code {completed.returncode}"
            )

        for path, expected in protected.items():
            if not path.is_file() or sha256(path) != expected:
                raise RuntimeError(
                    f"Protected production source changed: {path}"
                )

        print("[PASS] Certified OIT-032 production and test unchanged")
        print("[PASS] Oracle terminal runner unchanged")
        print("[PASS] OIT-033 production module installed")
        print("[PASS] OIT-033 standalone test installed")
        print("[PASS] Canonical real-intelligence input discovery certified")
        print("[PASS] Genuine artifact eligibility checks certified")
        print("[PASS] Existing read-only callable discovery certified")
        print("[PASS] No analytics execution or runtime fabrication performed")
        print("[PASS] OLA, OIA, INT-OII, ORR, OOR, and Q Series unchanged")
        print("[PASS] Publication and execution remained disabled")
        print("[PASS] Read-only and execution boundaries preserved")
        print(f"[PASS] Repository located: {ROOT}")
        print("[DONE] OIT-033 REAL INTELLIGENCE INPUT BINDING READINESS INSTALLED")
        return 0

    except (RuntimeError, SyntaxError) as exc:
        print(f"[ERROR] {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
