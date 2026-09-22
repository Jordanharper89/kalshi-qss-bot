from __future__ import annotations
import ast, hashlib, subprocess, sys
from pathlib import Path

def locate_repository():
    here = Path(__file__).resolve().parent
    candidates = [Path.cwd().resolve(), here]
    for base in tuple(candidates):
        candidates.extend(base.parents)
    for root in candidates:
        root = root.resolve()
        p = root / "qseries_v2" / "oracle_terminal" / "oracle_real_intelligence_input_binding_readiness_gate.py"
        t = root / "test_oit_033_oracle_real_intelligence_input_binding_readiness_gate.py"
        if p.is_file() and t.is_file():
            return root
    raise SystemExit("[ERROR] Could not locate current Q Series repository.")

ROOT = locate_repository()
PACKAGE = ROOT / "qseries_v2" / "oracle_terminal"
OIT_033 = PACKAGE / "oracle_real_intelligence_input_binding_readiness_gate.py"
OIT_033_TEST = ROOT / "test_oit_033_oracle_real_intelligence_input_binding_readiness_gate.py"
PRODUCTION = PACKAGE / "oracle_real_intelligence_input_binding_authorization_gate.py"
TEST = ROOT / "test_oit_034_oracle_real_intelligence_input_binding_authorization_gate.py"
RUNNER = ROOT / "run_oracle_open_intelligence_terminal.py"
INIT = PACKAGE / "__init__.py"
PRODUCTION_SOURCE = '\nfrom __future__ import annotations\nimport hashlib, json\nfrom dataclasses import asdict, dataclass\nfrom pathlib import Path\nfrom typing import Any, Mapping\nfrom .oracle_real_intelligence_input_binding_readiness_gate import (\n    OracleRealIntelligenceBindingReadinessReport,\n    build_real_intelligence_binding_readiness_report,\n    verify_real_intelligence_binding_readiness_report,\n)\n\nSCHEMA_VERSION = "OIT-034"\nENGINE_ID = "OIT-034"\nPOLICY_ID = "oracle.real-intelligence-input-binding-authorization.v1"\n\nclass OracleRealIntelligenceAuthorizationInvariantError(RuntimeError):\n    pass\n\n@dataclass(frozen=True)\nclass OracleAuthorizedArtifact:\n    relative_path: str\n    byte_count: int\n    sha256: str\n    source_candidate_hash: str\n    authorization_granted: bool\n    authorization_hash: str\n\n@dataclass(frozen=True)\nclass OracleAuthorizedCallable:\n    module_name: str\n    callable_name: str\n    signature: tuple[str, ...]\n    source_candidate_hash: str\n    authorization_granted: bool\n    authorization_hash: str\n\n@dataclass(frozen=True)\nclass OracleRealIntelligenceAuthorizationReport:\n    schema_version: str\n    engine_id: str\n    policy_id: str\n    status: str\n    repository_root: str\n    readiness_report_hash: str\n    authorized_artifact: OracleAuthorizedArtifact | None\n    authorized_callable: OracleAuthorizedCallable | None\n    exact_artifact_hash_required: bool\n    exact_artifact_byte_count_required: bool\n    read_only_invocation_required: bool\n    lower_level_bypass_allowed: bool\n    persistence_allowed: bool\n    analytics_execution_allowed: bool\n    database_access_allowed: bool\n    networking_allowed: bool\n    publication_allowed: bool\n    action_authorization_allowed: bool\n    qseries_execution_allowed: bool\n    real_input_binding_authorized: bool\n    read_only: bool\n    failure_reason: str | None\n    report_hash: str\n\ndef _canonical(value: Any) -> Any:\n    if hasattr(value, "__dataclass_fields__"):\n        return _canonical(asdict(value))\n    if isinstance(value, Mapping):\n        return {str(k): _canonical(v) for k, v in sorted(value.items(), key=lambda p: str(p[0]))}\n    if isinstance(value, (tuple, list)):\n        return [_canonical(v) for v in value]\n    if isinstance(value, Path):\n        return value.as_posix()\n    if value is None or isinstance(value, (str, int, float, bool)):\n        return value\n    return repr(value)\n\ndef _hash(value: Any) -> str:\n    return hashlib.sha256(json.dumps(_canonical(value), sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()).hexdigest()\n\ndef _select_artifact(source):\n    items = sorted(\n        (x for x in source.artifact_candidates if x.candidate_eligible),\n        key=lambda x: (x.relative_path, x.sha256, x.byte_count, x.candidate_hash),\n    )\n    return items[0] if items else None\n\ndef _select_callable(source):\n    items = sorted(\n        (x for x in source.callable_candidates if x.candidate_eligible),\n        key=lambda x: (x.module_name, x.callable_name, x.candidate_hash),\n    )\n    return items[0] if items else None\n\ndef build_real_intelligence_binding_authorization_report(\n    repository_root: str | Path,\n    *,\n    readiness_report: OracleRealIntelligenceBindingReadinessReport | None = None,\n) -> OracleRealIntelligenceAuthorizationReport:\n    root = Path(repository_root).resolve()\n    source = readiness_report or build_real_intelligence_binding_readiness_report(root)\n    verify_real_intelligence_binding_readiness_report(source)\n\n    artifact_source = _select_artifact(source)\n    callable_source = _select_callable(source)\n\n    artifact = None\n    if artifact_source is not None:\n        body = {\n            "relative_path": artifact_source.relative_path,\n            "byte_count": artifact_source.byte_count,\n            "sha256": artifact_source.sha256,\n            "source_candidate_hash": artifact_source.candidate_hash,\n            "authorization_granted": bool(\n                artifact_source.candidate_eligible\n                and artifact_source.byte_count > 0\n                and len(artifact_source.sha256) == 64\n            ),\n        }\n        artifact = OracleAuthorizedArtifact(**body, authorization_hash=_hash(body))\n\n    callable_item = None\n    if callable_source is not None:\n        body = {\n            "module_name": callable_source.module_name,\n            "callable_name": callable_source.callable_name,\n            "signature": tuple(callable_source.signature),\n            "source_candidate_hash": callable_source.candidate_hash,\n            "authorization_granted": bool(\n                callable_source.candidate_eligible\n                and callable_source.read_only_name_signal\n                and not callable_source.persistence_name_signal\n            ),\n        }\n        callable_item = OracleAuthorizedCallable(**body, authorization_hash=_hash(body))\n\n    authorized = bool(\n        source.real_input_binding_ready\n        and artifact is not None and artifact.authorization_granted\n        and callable_item is not None and callable_item.authorization_granted\n    )\n    body = {\n        "schema_version": SCHEMA_VERSION,\n        "engine_id": ENGINE_ID,\n        "policy_id": POLICY_ID,\n        "status": "certified_read_only",\n        "repository_root": str(root),\n        "readiness_report_hash": source.report_hash,\n        "authorized_artifact": artifact,\n        "authorized_callable": callable_item,\n        "exact_artifact_hash_required": True,\n        "exact_artifact_byte_count_required": True,\n        "read_only_invocation_required": True,\n        "lower_level_bypass_allowed": False,\n        "persistence_allowed": False,\n        "analytics_execution_allowed": False,\n        "database_access_allowed": False,\n        "networking_allowed": False,\n        "publication_allowed": False,\n        "action_authorization_allowed": False,\n        "qseries_execution_allowed": False,\n        "real_input_binding_authorized": authorized,\n        "read_only": True,\n        "failure_reason": None if authorized else "real_input_binding_not_authorized",\n    }\n    report = OracleRealIntelligenceAuthorizationReport(**body, report_hash=_hash(body))\n    verify_real_intelligence_binding_authorization_report(report)\n    return report\n\ndef verify_real_intelligence_binding_authorization_report(report) -> bool:\n    body = asdict(report)\n    supplied = body.pop("report_hash")\n    if _hash(body) != supplied:\n        raise OracleRealIntelligenceAuthorizationInvariantError("authorization report hash mismatch")\n    if report.schema_version != SCHEMA_VERSION or report.policy_id != POLICY_ID:\n        raise OracleRealIntelligenceAuthorizationInvariantError("authorization identity mismatch")\n    if not report.read_only:\n        raise OracleRealIntelligenceAuthorizationInvariantError("authorization report is not read-only")\n    if (\n        report.lower_level_bypass_allowed\n        or report.persistence_allowed\n        or report.analytics_execution_allowed\n        or report.database_access_allowed\n        or report.networking_allowed\n        or report.publication_allowed\n        or report.action_authorization_allowed\n        or report.qseries_execution_allowed\n    ):\n        raise OracleRealIntelligenceAuthorizationInvariantError("forbidden capability enabled")\n    if not (\n        report.exact_artifact_hash_required\n        and report.exact_artifact_byte_count_required\n        and report.read_only_invocation_required\n    ):\n        raise OracleRealIntelligenceAuthorizationInvariantError("required authorization control missing")\n    if report.authorized_artifact is not None:\n        body = asdict(report.authorized_artifact)\n        supplied = body.pop("authorization_hash")\n        if _hash(body) != supplied:\n            raise OracleRealIntelligenceAuthorizationInvariantError("artifact authorization hash mismatch")\n    if report.authorized_callable is not None:\n        body = asdict(report.authorized_callable)\n        supplied = body.pop("authorization_hash")\n        if _hash(body) != supplied:\n            raise OracleRealIntelligenceAuthorizationInvariantError("callable authorization hash mismatch")\n    expected = bool(\n        report.authorized_artifact\n        and report.authorized_artifact.authorization_granted\n        and report.authorized_callable\n        and report.authorized_callable.authorization_granted\n    )\n    if report.real_input_binding_authorized != expected:\n        raise OracleRealIntelligenceAuthorizationInvariantError("authorization state mismatch")\n    return True\n'
TEST_SOURCE = '\nfrom __future__ import annotations\nfrom dataclasses import replace\nfrom pathlib import Path\nfrom tempfile import TemporaryDirectory\nfrom qseries_v2.oracle_terminal.oracle_real_intelligence_input_binding_readiness_gate import (\n    ENGINE_ID as E33, POLICY_ID as P33, SCHEMA_VERSION as S33,\n    OracleRealIntelligenceArtifactCandidate,\n    OracleRealIntelligenceCallableCandidate,\n    OracleRealIntelligenceBindingReadinessReport,\n    _stable_hash as h33,\n    verify_real_intelligence_binding_readiness_report,\n)\nfrom qseries_v2.oracle_terminal.oracle_real_intelligence_input_binding_authorization_gate import (\n    OracleRealIntelligenceAuthorizationInvariantError,\n    build_real_intelligence_binding_authorization_report,\n    verify_real_intelligence_binding_authorization_report,\n)\n\ndef make_source(root):\n    ab = {\n        "relative_path": "runtime/oracle_intelligence/genuine.json",\n        "byte_count": 42,\n        "sha256": "a" * 64,\n        "suffix": ".json",\n        "hidden": False,\n        "forbidden_suffix": False,\n        "readable": True,\n        "candidate_eligible": True,\n    }\n    artifact = OracleRealIntelligenceArtifactCandidate(**ab, candidate_hash=h33(ab))\n    cb = {\n        "module_name": "qseries_v2.oracle_terminal.oracle_genuine_intelligence_artifact_admission",\n        "callable_name": "load_genuine_intelligence_artifact",\n        "signature": ("repository_root", "artifact_path"),\n        "importable": True,\n        "callable_resolved": True,\n        "read_only_name_signal": True,\n        "persistence_name_signal": False,\n        "candidate_eligible": True,\n    }\n    callable_item = OracleRealIntelligenceCallableCandidate(**cb, candidate_hash=h33(cb))\n    body = {\n        "schema_version": S33,\n        "engine_id": E33,\n        "policy_id": P33,\n        "status": "certified_read_only",\n        "repository_root": str(root.resolve()),\n        "runtime_root": str((root / "runtime" / "oracle_intelligence").resolve()),\n        "runtime_root_exists": True,\n        "artifact_candidates": (artifact,),\n        "artifact_candidate_count": 1,\n        "eligible_artifact_count": 1,\n        "callable_candidates": (callable_item,),\n        "callable_candidate_count": 1,\n        "eligible_callable_count": 1,\n        "canonical_runtime_target_verified": True,\n        "genuine_artifact_available": True,\n        "read_only_callable_available": True,\n        "real_input_binding_ready": True,\n        "analytics_execution_performed": False,\n        "database_access_performed": False,\n        "runtime_artifact_created": False,\n        "publication_allowed": False,\n        "action_authorization_allowed": False,\n        "qseries_execution_allowed": False,\n        "read_only": True,\n        "failure_reason": None,\n    }\n    report = OracleRealIntelligenceBindingReadinessReport(**body, report_hash=h33(body))\n    verify_real_intelligence_binding_readiness_report(report)\n    return report\n\ndef main():\n    print("=" * 48)\n    print(" OIT-034 TEST")\n    print(" REAL INTELLIGENCE INPUT BINDING AUTHORIZATION")\n    print("=" * 48)\n    with TemporaryDirectory() as temporary:\n        root = Path(temporary)\n        source = make_source(root)\n        report = build_real_intelligence_binding_authorization_report(root, readiness_report=source)\n        assert report.real_input_binding_authorized\n        assert report.authorized_artifact.sha256 == "a" * 64\n        assert report.authorized_artifact.byte_count == 42\n        assert report.authorized_callable.callable_name == "load_genuine_intelligence_artifact"\n        assert report.exact_artifact_hash_required\n        assert report.exact_artifact_byte_count_required\n        assert report.read_only_invocation_required\n        assert not report.persistence_allowed\n        assert not report.analytics_execution_allowed\n        assert not report.database_access_allowed\n        assert not report.networking_allowed\n        assert not report.publication_allowed\n        assert not report.action_authorization_allowed\n        assert not report.qseries_execution_allowed\n        assert verify_real_intelligence_binding_authorization_report(report)\n        assert build_real_intelligence_binding_authorization_report(root, readiness_report=source) == report\n        try:\n            verify_real_intelligence_binding_authorization_report(replace(report, persistence_allowed=True))\n        except OracleRealIntelligenceAuthorizationInvariantError:\n            pass\n        else:\n            raise AssertionError("tampered authorization accepted")\n    print("[PASS] Certified OIT-033 readiness consumed")\n    print("[PASS] Exact artifact path, SHA-256, and byte count authorized")\n    print("[PASS] Exact read-only callable authorized")\n    print("[PASS] Lower-level bypass and persistence denied")\n    print("[PASS] Database, networking, analytics, publication, action, and Q Series execution denied")\n    print("[PASS] Authorization deterministic across replay")\n    print("[PASS] Tampered authorization rejected")\n    print("[DONE] OIT-034 REAL INTELLIGENCE INPUT BINDING AUTHORIZATION PASS")\n    return 0\n\nif __name__ == "__main__":\n    raise SystemExit(main())\n'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def require(path, tokens, label):
    if not path.is_file():
        raise RuntimeError(f"{label} missing: {path}")
    source = path.read_text(encoding="utf-8")
    missing = [x for x in tokens if x not in source]
    if missing:
        raise RuntimeError(f"{label} contract mismatch: {missing}")

def write(path, source):
    path.write_text(source.lstrip(), encoding="utf-8", newline="\n")
    ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    print(f"[OK] FULL REPLACEMENT: {path.resolve()}")

def main():
    print("=" * 48)
    print(" OIT-034 INSTALLER")
    print(" REAL INTELLIGENCE INPUT BINDING AUTHORIZATION")
    print("=" * 48)
    try:
        require(OIT_033, (
            'SCHEMA_VERSION = "OIT-033"',
            'POLICY_ID = "oracle.real-intelligence-input-binding-readiness.v1"',
            "OracleRealIntelligenceBindingReadinessReport",
            "build_real_intelligence_binding_readiness_report",
            "verify_real_intelligence_binding_readiness_report",
            "real_input_binding_ready",
        ), "Certified OIT-033 production")
        require(OIT_033_TEST, (
            "OIT-033 TEST",
            "REAL INTELLIGENCE INPUT BINDING READINESS",
            "OIT-033 REAL INTELLIGENCE INPUT BINDING READINESS PASS",
        ), "Certified OIT-033 standalone test")
        if not RUNNER.is_file():
            raise RuntimeError(f"Oracle terminal runner missing: {RUNNER}")

        protected = {OIT_033: sha(OIT_033), OIT_033_TEST: sha(OIT_033_TEST), RUNNER: sha(RUNNER)}
        print("[OK] Certified OIT-033 production contract verified")
        print("[OK] Certified OIT-033 standalone test verified")
        print("[OK] Oracle terminal runner located")

        upstream = subprocess.run([sys.executable, str(OIT_033_TEST)], cwd=ROOT, check=False)
        if upstream.returncode:
            raise RuntimeError(f"OIT-033 certification failed with exit code {upstream.returncode}")

        write(PRODUCTION, PRODUCTION_SOURCE)
        write(TEST, TEST_SOURCE)

        export = "from .oracle_real_intelligence_input_binding_authorization_gate import *"
        current = INIT.read_text(encoding="utf-8") if INIT.exists() else ""
        if export not in current.splitlines():
            if current and not current.endswith("\n"):
                current += "\n"
            INIT.write_text(current + export + "\n", encoding="utf-8", newline="\n")
            print(f"[OK] PACKAGE UPDATED: {INIT.resolve()}")
        else:
            print(f"[OK] PACKAGE EXPORT PRESENT: {INIT.resolve()}")

        result = subprocess.run([sys.executable, str(TEST)], cwd=ROOT, check=False)
        if result.returncode:
            raise RuntimeError(f"OIT-034 test failed with exit code {result.returncode}")

        for path, expected in protected.items():
            if sha(path) != expected:
                raise RuntimeError(f"Protected source changed: {path}")

        print("[PASS] Certified OIT-033 production and test unchanged")
        print("[PASS] Oracle terminal runner unchanged")
        print("[PASS] OIT-034 production module installed")
        print("[PASS] OIT-034 standalone test installed")
        print("[PASS] Exact artifact and read-only callable authorization certified")
        print("[PASS] Persistence, database, networking, publication, action, and execution denied")
        print("[PASS] Read-only and execution boundaries preserved")
        print(f"[PASS] Repository located: {ROOT}")
        print("[DONE] OIT-034 REAL INTELLIGENCE INPUT BINDING AUTHORIZATION INSTALLED")
        return 0
    except (RuntimeError, SyntaxError) as exc:
        print(f"[ERROR] {exc}")
        return 1

if __name__ == "__main__":
    raise SystemExit(main())
