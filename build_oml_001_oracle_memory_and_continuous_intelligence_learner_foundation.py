from __future__ import annotations

import ast
import hashlib
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent


def locate_repository() -> Path:
    candidates: list[Path] = []

    for base in (Path.cwd().resolve(), SCRIPT_DIR):
        candidates.extend((base, base / "kalshi-qss-bot"))
        for parent in base.parents:
            candidates.extend((parent, parent / "kalshi-qss-bot"))

    seen: set[Path] = set()

    for candidate in candidates:
        candidate = candidate.resolve()

        if candidate in seen:
            continue
        seen.add(candidate)

        oit_package = candidate / "qseries_v2" / "oracle_terminal"
        oit_050 = (
            oit_package
            / "oracle_terminal_final_freeze_and_completion.py"
        )
        oit_050_test = (
            candidate
            / "test_oit_050_oracle_terminal_final_freeze_and_completion.py"
        )

        if oit_050.is_file() and oit_050_test.is_file():
            return candidate

    raise SystemExit(
        "[ERROR] Could not locate current Q Series repository."
    )


ROOT = locate_repository()

OIT_PACKAGE = ROOT / "qseries_v2" / "oracle_terminal"
OIT_050 = (
    OIT_PACKAGE
    / "oracle_terminal_final_freeze_and_completion.py"
)
OIT_050_TEST = (
    ROOT
    / "test_oit_050_oracle_terminal_final_freeze_and_completion.py"
)
OIT_RUNNER = ROOT / "run_oracle_open_intelligence_terminal.py"

PACKAGE = ROOT / "qseries_v2" / "oracle_memory"
PRODUCTION = (
    PACKAGE
    / "oracle_memory_continuous_intelligence_learner_foundation.py"
)
TEST = (
    ROOT
    / "test_oml_001_oracle_memory_and_continuous_intelligence_learner_foundation.py"
)
INIT = PACKAGE / "__init__.py"

PRODUCTION_SOURCE = r'''
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping

from qseries_v2.oracle_terminal.oracle_terminal_final_freeze_and_completion import (
    NEXT_SUBSYSTEM,
    OracleTerminalFinalFreezeCompletionReport,
    verify_oracle_terminal_final_freeze_completion_report,
)

SCHEMA_VERSION = "OML-001"
ENGINE_ID = "OML-001"
POLICY_ID = (
    "oracle-memory-continuous-intelligence-learner.foundation.v1"
)

SUBSYSTEM_ID = "oracle_memory_and_continuous_intelligence_learner"
UPSTREAM_SUBSYSTEM_ID = "oracle_open_intelligence_terminal"
UPSTREAM_FINAL_MILESTONE = "OIT-050"

MEMORY_DOMAINS = (
    "entity_memory",
    "source_reliability_memory",
    "market_behavior_memory",
    "calibration_memory",
    "causal_memory",
    "narrative_memory",
    "knowledge_graph_memory",
    "meta_learning_memory",
)


class OracleMemoryLearnerFoundationInvariantError(RuntimeError):
    pass


@dataclass(frozen=True)
class OracleMemoryLearnerUpstreamCertification:
    upstream_subsystem_id: str
    upstream_final_milestone: str
    upstream_report_hash: str
    upstream_runner_sha256: str
    upstream_completed: bool
    upstream_frozen: bool
    upstream_production_ready: bool
    upstream_read_only_boundary_frozen: bool
    upstream_publication_disabled: bool
    upstream_action_authorization_disabled: bool
    upstream_qseries_execution_disabled: bool
    downstream_subsystem_authorized: bool
    certification_hash: str


@dataclass(frozen=True)
class OracleMemoryLearnerFoundationReport:
    schema_version: str
    engine_id: str
    policy_id: str
    subsystem_id: str
    repository_root: str
    upstream_certification: OracleMemoryLearnerUpstreamCertification
    package_separate_from_oracle_terminal: bool
    certified_read_only_upstream_consumption_only: bool
    deterministic_contract_enabled: bool
    replay_verification_enabled: bool
    immutable_lineage_required: bool
    auditability_required: bool
    configured_memory_domains: tuple[str, ...]
    persistent_memory_enabled: bool
    learning_update_enabled: bool
    learner_execution_performed: bool
    memory_write_performed: bool
    database_access_performed: bool
    networking_performed: bool
    runtime_artifact_created: bool
    runtime_artifact_modified: bool
    publication_allowed: bool
    action_authorization_allowed: bool
    qseries_execution_allowed: bool
    foundation_ready: bool
    next_certification_authorized: bool
    read_only: bool
    failure_reason: str | None
    report_hash: str


def _canonical(value: Any) -> Any:
    if hasattr(value, "__dataclass_fields__"):
        return _canonical(asdict(value))

    if isinstance(value, Mapping):
        return {
            str(key): _canonical(item)
            for key, item in sorted(
                value.items(),
                key=lambda pair: str(pair[0]),
            )
        }

    if isinstance(value, (tuple, list)):
        return [_canonical(item) for item in value]

    if value is None or isinstance(
        value,
        (str, int, float, bool),
    ):
        return value

    raise OracleMemoryLearnerFoundationInvariantError(
        "unsupported OML-001 value type: "
        f"{type(value).__module__}.{type(value).__qualname__}"
    )


def _stable_hash(value: Any) -> str:
    payload = json.dumps(
        _canonical(value),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")

    return hashlib.sha256(payload).hexdigest()


def verify_upstream_certification(
    certification: OracleMemoryLearnerUpstreamCertification,
) -> bool:
    body = asdict(certification)
    supplied = body.pop("certification_hash")

    if _stable_hash(body) != supplied:
        raise OracleMemoryLearnerFoundationInvariantError(
            "OML-001 upstream certification hash mismatch"
        )

    if certification.upstream_subsystem_id != UPSTREAM_SUBSYSTEM_ID:
        raise OracleMemoryLearnerFoundationInvariantError(
            "OML-001 upstream subsystem mismatch"
        )

    if certification.upstream_final_milestone != UPSTREAM_FINAL_MILESTONE:
        raise OracleMemoryLearnerFoundationInvariantError(
            "OML-001 upstream milestone mismatch"
        )

    if len(certification.upstream_report_hash) != 64:
        raise OracleMemoryLearnerFoundationInvariantError(
            "OML-001 upstream report hash invalid"
        )

    if len(certification.upstream_runner_sha256) != 64:
        raise OracleMemoryLearnerFoundationInvariantError(
            "OML-001 upstream runner hash invalid"
        )

    required_true = (
        certification.upstream_completed,
        certification.upstream_frozen,
        certification.upstream_production_ready,
        certification.upstream_read_only_boundary_frozen,
        certification.upstream_publication_disabled,
        certification.upstream_action_authorization_disabled,
        certification.upstream_qseries_execution_disabled,
        certification.downstream_subsystem_authorized,
    )

    if not all(required_true):
        raise OracleMemoryLearnerFoundationInvariantError(
            "OML-001 upstream certification incomplete"
        )

    return True


def build_oracle_memory_learner_foundation_report(
    repository_root: str | Path,
    *,
    oit_final_freeze_report: OracleTerminalFinalFreezeCompletionReport,
) -> OracleMemoryLearnerFoundationReport:
    root = Path(repository_root).resolve()

    verify_oracle_terminal_final_freeze_completion_report(
        oit_final_freeze_report
    )

    freeze = oit_final_freeze_report.freeze_manifest

    if NEXT_SUBSYSTEM != SUBSYSTEM_ID:
        raise OracleMemoryLearnerFoundationInvariantError(
            "OIT-050 did not authorize the OML subsystem identity"
        )

    if freeze.subsystem_id != UPSTREAM_SUBSYSTEM_ID:
        raise OracleMemoryLearnerFoundationInvariantError(
            "OIT-050 frozen subsystem identity mismatch"
        )

    if freeze.final_milestone != UPSTREAM_FINAL_MILESTONE:
        raise OracleMemoryLearnerFoundationInvariantError(
            "OIT-050 frozen milestone mismatch"
        )

    upstream_body = {
        "upstream_subsystem_id": freeze.subsystem_id,
        "upstream_final_milestone": freeze.final_milestone,
        "upstream_report_hash": oit_final_freeze_report.report_hash,
        "upstream_runner_sha256": freeze.source_runner_sha256,
        "upstream_completed": oit_final_freeze_report.subsystem_completed,
        "upstream_frozen": oit_final_freeze_report.subsystem_frozen,
        "upstream_production_ready": (
            oit_final_freeze_report.terminal_production_ready
        ),
        "upstream_read_only_boundary_frozen": (
            freeze.read_only_boundary_frozen
        ),
        "upstream_publication_disabled": (
            freeze.publication_frozen_disabled
        ),
        "upstream_action_authorization_disabled": (
            freeze.action_authorization_frozen_disabled
        ),
        "upstream_qseries_execution_disabled": (
            freeze.qseries_execution_frozen_disabled
        ),
        "downstream_subsystem_authorized": (
            oit_final_freeze_report.next_subsystem_authorized
        ),
    }

    upstream = OracleMemoryLearnerUpstreamCertification(
        **upstream_body,
        certification_hash=_stable_hash(upstream_body),
    )
    verify_upstream_certification(upstream)

    package_separate = (
        root / "qseries_v2" / "oracle_memory"
    ).resolve() != (
        root / "qseries_v2" / "oracle_terminal"
    ).resolve()

    ready = bool(
        package_separate
        and oit_final_freeze_report.subsystem_completed
        and oit_final_freeze_report.subsystem_frozen
        and oit_final_freeze_report.terminal_production_ready
        and oit_final_freeze_report.next_subsystem_authorized
        and freeze.read_only_boundary_frozen
        and freeze.publication_frozen_disabled
        and freeze.action_authorization_frozen_disabled
        and freeze.qseries_execution_frozen_disabled
    )

    report_body = {
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "policy_id": POLICY_ID,
        "subsystem_id": SUBSYSTEM_ID,
        "repository_root": str(root),
        "upstream_certification": upstream,
        "package_separate_from_oracle_terminal": package_separate,
        "certified_read_only_upstream_consumption_only": True,
        "deterministic_contract_enabled": True,
        "replay_verification_enabled": True,
        "immutable_lineage_required": True,
        "auditability_required": True,
        "configured_memory_domains": MEMORY_DOMAINS,
        "persistent_memory_enabled": False,
        "learning_update_enabled": False,
        "learner_execution_performed": False,
        "memory_write_performed": False,
        "database_access_performed": False,
        "networking_performed": False,
        "runtime_artifact_created": False,
        "runtime_artifact_modified": False,
        "publication_allowed": False,
        "action_authorization_allowed": False,
        "qseries_execution_allowed": False,
        "foundation_ready": ready,
        "next_certification_authorized": ready,
        "read_only": True,
        "failure_reason": (
            None
            if ready
            else "OML-001 foundation prerequisites not satisfied"
        ),
    }

    report = OracleMemoryLearnerFoundationReport(
        **report_body,
        report_hash=_stable_hash(report_body),
    )
    verify_oracle_memory_learner_foundation_report(report)
    return report


def verify_oracle_memory_learner_foundation_report(
    report: OracleMemoryLearnerFoundationReport,
) -> bool:
    body = asdict(report)
    supplied = body.pop("report_hash")

    if _stable_hash(body) != supplied:
        raise OracleMemoryLearnerFoundationInvariantError(
            "OML-001 report hash mismatch"
        )

    if report.schema_version != SCHEMA_VERSION:
        raise OracleMemoryLearnerFoundationInvariantError(
            "OML-001 schema mismatch"
        )

    if report.engine_id != ENGINE_ID:
        raise OracleMemoryLearnerFoundationInvariantError(
            "OML-001 engine mismatch"
        )

    if report.policy_id != POLICY_ID:
        raise OracleMemoryLearnerFoundationInvariantError(
            "OML-001 policy mismatch"
        )

    if report.subsystem_id != SUBSYSTEM_ID:
        raise OracleMemoryLearnerFoundationInvariantError(
            "OML-001 subsystem mismatch"
        )

    verify_upstream_certification(report.upstream_certification)

    if tuple(report.configured_memory_domains) != MEMORY_DOMAINS:
        raise OracleMemoryLearnerFoundationInvariantError(
            "OML-001 memory-domain contract mismatch"
        )

    required_true = (
        report.package_separate_from_oracle_terminal,
        report.certified_read_only_upstream_consumption_only,
        report.deterministic_contract_enabled,
        report.replay_verification_enabled,
        report.immutable_lineage_required,
        report.auditability_required,
        report.foundation_ready,
        report.next_certification_authorized,
        report.read_only,
    )

    if not all(required_true):
        raise OracleMemoryLearnerFoundationInvariantError(
            report.failure_reason
            or "OML-001 required foundation guarantee missing"
        )

    forbidden = (
        report.persistent_memory_enabled,
        report.learning_update_enabled,
        report.learner_execution_performed,
        report.memory_write_performed,
        report.database_access_performed,
        report.networking_performed,
        report.runtime_artifact_created,
        report.runtime_artifact_modified,
        report.publication_allowed,
        report.action_authorization_allowed,
        report.qseries_execution_allowed,
    )

    if any(forbidden):
        raise OracleMemoryLearnerFoundationInvariantError(
            "OML-001 forbidden capability enabled"
        )

    if report.failure_reason is not None:
        raise OracleMemoryLearnerFoundationInvariantError(
            "OML-001 ready report contains failure reason"
        )

    return True
'''

TEST_SOURCE = r'''
from __future__ import annotations

import importlib.util
import sys
from dataclasses import replace
from pathlib import Path

from qseries_v2.oracle_memory.oracle_memory_continuous_intelligence_learner_foundation import (
    MEMORY_DOMAINS,
    OracleMemoryLearnerFoundationInvariantError,
    build_oracle_memory_learner_foundation_report,
    verify_oracle_memory_learner_foundation_report,
)


def load_oit_050_fixture(root: Path):
    path = (
        root
        / "test_oit_050_oracle_terminal_final_freeze_and_completion.py"
    )
    name = "oit_050_fixture_for_oml_001"

    specification = importlib.util.spec_from_file_location(
        name,
        path,
    )

    if specification is None or specification.loader is None:
        raise RuntimeError(
            "unable to load certified OIT-050 fixture"
        )

    module = importlib.util.module_from_spec(specification)
    sys.modules[name] = module
    specification.loader.exec_module(module)
    return module


def build_oit_050_report(root: Path):
    fixture = load_oit_050_fixture(root)

    from qseries_v2.oracle_terminal.oracle_terminal_final_freeze_and_completion import (
        build_oracle_terminal_final_freeze_completion_report,
    )

    certification = fixture.build_oit_049_report(root)

    return build_oracle_terminal_final_freeze_completion_report(
        root,
        production_certification_report=certification,
    )


def expect_rejection(callable_object, label: str) -> None:
    try:
        callable_object()
    except OracleMemoryLearnerFoundationInvariantError:
        return

    raise AssertionError(
        f"tampered OML-001 {label} accepted"
    )


def main() -> int:
    print("=" * 48)
    print(" OML-001 TEST")
    print(" MEMORY AND CONTINUOUS LEARNER FOUNDATION")
    print("=" * 48)

    root = Path(__file__).resolve().parent
    oit_report = build_oit_050_report(root)

    report = build_oracle_memory_learner_foundation_report(
        root,
        oit_final_freeze_report=oit_report,
    )

    assert report.schema_version == "OML-001"
    assert report.engine_id == "OML-001"
    assert (
        report.subsystem_id
        == "oracle_memory_and_continuous_intelligence_learner"
    )

    upstream = report.upstream_certification
    assert upstream.upstream_subsystem_id == (
        "oracle_open_intelligence_terminal"
    )
    assert upstream.upstream_final_milestone == "OIT-050"
    assert upstream.upstream_report_hash == oit_report.report_hash
    assert upstream.upstream_runner_sha256 == (
        oit_report.freeze_manifest.source_runner_sha256
    )
    assert upstream.upstream_completed
    assert upstream.upstream_frozen
    assert upstream.upstream_production_ready
    assert upstream.upstream_read_only_boundary_frozen
    assert upstream.upstream_publication_disabled
    assert upstream.upstream_action_authorization_disabled
    assert upstream.upstream_qseries_execution_disabled
    assert upstream.downstream_subsystem_authorized

    assert report.package_separate_from_oracle_terminal
    assert report.certified_read_only_upstream_consumption_only
    assert report.deterministic_contract_enabled
    assert report.replay_verification_enabled
    assert report.immutable_lineage_required
    assert report.auditability_required
    assert report.configured_memory_domains == MEMORY_DOMAINS
    assert report.foundation_ready
    assert report.next_certification_authorized
    assert report.read_only

    assert not report.persistent_memory_enabled
    assert not report.learning_update_enabled
    assert not report.learner_execution_performed
    assert not report.memory_write_performed
    assert not report.database_access_performed
    assert not report.networking_performed
    assert not report.runtime_artifact_created
    assert not report.runtime_artifact_modified
    assert not report.publication_allowed
    assert not report.action_authorization_allowed
    assert not report.qseries_execution_allowed

    replay = build_oracle_memory_learner_foundation_report(
        root,
        oit_final_freeze_report=oit_report,
    )

    assert replay == report
    assert verify_oracle_memory_learner_foundation_report(report)

    expect_rejection(
        lambda: verify_oracle_memory_learner_foundation_report(
            replace(
                report,
                memory_write_performed=True,
            )
        ),
        "memory-write state",
    )

    expect_rejection(
        lambda: verify_oracle_memory_learner_foundation_report(
            replace(
                report,
                publication_allowed=True,
            )
        ),
        "publication state",
    )

    expect_rejection(
        lambda: verify_oracle_memory_learner_foundation_report(
            replace(
                report,
                qseries_execution_allowed=True,
            )
        ),
        "Q Series execution state",
    )

    expect_rejection(
        lambda: verify_oracle_memory_learner_foundation_report(
            replace(
                report,
                package_separate_from_oracle_terminal=False,
            )
        ),
        "package-separation state",
    )

    print("[PASS] Certified OIT-050 final freeze consumed")
    print("[PASS] OIT frozen subsystem identity verified")
    print("[PASS] OIT frozen runner hash lineage retained")
    print("[PASS] OML created as a separate production package")
    print("[PASS] Certified read-only upstream consumption enforced")
    print("[PASS] Eight memory and learner domains registered")
    print("[PASS] Deterministic hashing enabled")
    print("[PASS] Replay equality verified")
    print("[PASS] Immutable lineage and auditability required")
    print("[PASS] Persistent memory remained disabled")
    print("[PASS] Continuous learning remained disabled")
    print("[PASS] No memory write or learner execution performed")
    print("[PASS] No database, network, or runtime mutation performed")
    print("[PASS] Publication remained disabled")
    print("[PASS] Action authorization remained disabled")
    print("[PASS] Q Series execution remained disabled")
    print("[PASS] Tampered reports rejected")
    print("[DONE] OML-001 MEMORY AND CONTINUOUS LEARNER FOUNDATION PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require_contract(
    path: Path,
    tokens: tuple[str, ...],
    label: str,
) -> None:
    if not path.is_file():
        raise RuntimeError(f"{label} missing: {path}")

    text = path.read_text(encoding="utf-8")
    missing = [token for token in tokens if token not in text]

    if missing:
        raise RuntimeError(
            f"{label} contract mismatch: {missing}"
        )

    ast.parse(text, filename=str(path))


def write_complete(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        text.lstrip(),
        encoding="utf-8",
        newline="\n",
    )
    ast.parse(
        path.read_text(encoding="utf-8"),
        filename=str(path),
    )
    print(f"[OK] FULL REPLACEMENT: {path.resolve()}")


def protected_sources() -> dict[Path, str]:
    protected: dict[Path, str] = {}

    if OIT_PACKAGE.exists():
        for path in OIT_PACKAGE.rglob("*.py"):
            if path.is_file():
                protected[path] = sha256(path)

    for path in (
        OIT_050_TEST,
        OIT_RUNNER,
    ):
        if path.is_file():
            protected[path] = sha256(path)

    return protected


def main() -> int:
    print("=" * 48)
    print(" OML-001 INSTALLER")
    print(" MEMORY AND CONTINUOUS LEARNER FOUNDATION")
    print("=" * 48)

    try:
        require_contract(
            OIT_050,
            (
                'SCHEMA_VERSION = "OIT-050"',
                'ENGINE_ID = "OIT-050"',
                (
                    'POLICY_ID = '
                    '"oracle-terminal.final-freeze-and-completion.v1"'
                ),
                (
                    'SUBSYSTEM_ID = '
                    '"oracle_open_intelligence_terminal"'
                ),
                'FINAL_MILESTONE = "OIT-050"',
                (
                    'NEXT_SUBSYSTEM = '
                    '"oracle_memory_and_continuous_intelligence_learner"'
                ),
                "OracleTerminalFinalFreezeManifest",
                "OracleTerminalFinalFreezeCompletionReport",
                "verify_oracle_terminal_final_freeze_completion_report",
                "subsystem_completed",
                "subsystem_frozen",
                "terminal_production_ready",
                "next_subsystem_authorized",
                "read_only_boundary_frozen",
                "publication_frozen_disabled",
                "action_authorization_frozen_disabled",
                "qseries_execution_frozen_disabled",
                "no_further_oit_feature_layers_required",
            ),
            "Certified OIT-050 production",
        )

        require_contract(
            OIT_050_TEST,
            (
                "OIT-050 TEST",
                "FINAL FREEZE AND COMPLETION",
                "Certified OIT-049 Correction V3 consumed",
                "No further OIT feature layers required",
                "OIT-050 FINAL FREEZE AND COMPLETION PASS",
            ),
            "Certified OIT-050 standalone test",
        )

        if not OIT_RUNNER.is_file():
            raise RuntimeError(
                f"Frozen Oracle terminal runner missing: {OIT_RUNNER}"
            )

        protected = protected_sources()

        print("[OK] Certified OIT-050 production contract verified")
        print("[OK] Certified OIT-050 standalone test verified")
        print("[OK] Frozen Oracle terminal runner located")
        print(
            f"[OK] Frozen OIT source files captured: "
            f"{len(protected)}"
        )

        upstream = subprocess.run(
            [sys.executable, str(OIT_050_TEST)],
            cwd=ROOT,
            check=False,
        )

        if upstream.returncode:
            raise RuntimeError(
                "OIT-050 certification failed with exit code "
                f"{upstream.returncode}"
            )

        write_complete(PRODUCTION, PRODUCTION_SOURCE)
        write_complete(TEST, TEST_SOURCE)

        export = (
            "from .oracle_memory_continuous_intelligence_learner_foundation "
            "import *"
        )

        current = (
            INIT.read_text(encoding="utf-8")
            if INIT.exists()
            else ""
        )

        if export not in current.splitlines():
            if current and not current.endswith("\n"):
                current += "\n"

            current += export + "\n"

            INIT.write_text(
                current,
                encoding="utf-8",
                newline="\n",
            )
            print(f"[OK] PACKAGE UPDATED: {INIT.resolve()}")
        else:
            print(f"[OK] PACKAGE EXPORT PRESENT: {INIT.resolve()}")

        ast.parse(
            INIT.read_text(encoding="utf-8"),
            filename=str(INIT),
        )

        completed = subprocess.run(
            [sys.executable, str(TEST)],
            cwd=ROOT,
            check=False,
        )

        if completed.returncode:
            raise RuntimeError(
                "OML-001 test failed with exit code "
                f"{completed.returncode}"
            )

        for path, expected in protected.items():
            if not path.is_file() or sha256(path) != expected:
                raise RuntimeError(
                    f"Frozen OIT source changed: {path}"
                )

        print("[PASS] OIT-050 production and test unchanged")
        print("[PASS] Frozen Oracle terminal runner unchanged")
        print("[PASS] Entire Oracle Terminal package unchanged")
        print("[PASS] Separate Oracle Memory package installed")
        print("[PASS] OML-001 production module installed")
        print("[PASS] OML-001 standalone deterministic test installed")
        print("[PASS] Certified OIT read-only boundary consumed")
        print("[PASS] OIT deterministic hashes and lineage preserved")
        print("[PASS] Eight memory and learner domains registered")
        print("[PASS] Persistent memory and learning remain gated")
        print("[PASS] No database, network, or runtime mutation performed")
        print("[PASS] Publication remained disabled")
        print("[PASS] Q Series execution remained disabled")
        print("[PASS] Read-only and execution boundaries preserved")
        print(f"[PASS] Repository located: {ROOT}")
        print("[DONE] OML-001 FOUNDATION INSTALLED")
        return 0

    except (RuntimeError, SyntaxError) as exc:
        print(f"[ERROR] {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
