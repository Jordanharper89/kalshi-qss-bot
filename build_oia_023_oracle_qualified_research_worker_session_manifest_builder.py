from __future__ import annotations

import ast
import subprocess
import sys
from pathlib import Path

MODULE_SOURCE = 'from __future__ import annotations\n\nimport argparse\nimport hashlib\nimport json\nimport os\nimport tempfile\nfrom dataclasses import asdict, dataclass, is_dataclass\nfrom datetime import datetime, timezone\nfrom pathlib import Path\nfrom types import MappingProxyType\nfrom typing import Any, Mapping\n\nfrom .oracle_qualified_research_priority_ranking_engine import RANKING_POLICY_ID\nfrom .oracle_qualified_research_priority_tier_assignment_gate import TIER_POLICY_ID\nfrom .oracle_qualified_research_queue_admission_gate import QUEUE_POLICY_ID\nfrom .oracle_qualified_research_work_item_materialization_engine import WORK_ITEM_POLICY_ID\nfrom .oracle_qualified_research_dispatch_manifest_builder import DISPATCH_POLICY_ID\nfrom .oracle_qualified_research_dispatch_claim_gate import CLAIM_POLICY_ID\nfrom .oracle_qualified_research_claim_activation_gate import (\n    ACTIVATION_POLICY_ID,\n    ACTIVATION_READY,\n    ENTRY_ACTIVATED,\n    DEFAULT_ACTIVATION_DIRECTORY,\n    stable_hash as activation_stable_hash,\n)\n\nSCHEMA_VERSION = "OIA-023"\nENGINE_ID = "OIA-023"\nSESSION_POLICY_ID = "oracle.qualified-research-worker-session-manifest.v1"\n\nSESSION_READY = "session_ready"\nSESSION_ENTRY_READY = "session_entry_ready"\n\nREAD_ONLY_CORPUS = True\nRESEARCH_EXECUTION_ALLOWED = False\nEXECUTION_ALLOWED = False\nALERTS_ALLOWED = False\nQSERIES_HANDOFF_ALLOWED = False\nSIGNALS_ALLOWED = False\nTRADING_RECOMMENDATIONS_ALLOWED = False\nSOURCE_MUTATION_ALLOWED = False\nMARKET_ORDER_CREATION_ALLOWED = False\nFUNDS_MOVEMENT_ALLOWED = False\nPORTFOLIO_MUTATION_ALLOWED = False\nSESSION_ARTIFACT_PERSISTENCE_ALLOWED = True\n\nDEFAULT_SESSION_DIRECTORY = (\n    Path("runtime")\n    / "oracle_intelligence"\n    / "qualified_research_worker_sessions"\n)\n\n\nclass QualifiedResearchWorkerSessionError(RuntimeError):\n    pass\n\n\nclass QualifiedResearchWorkerSessionInvariantError(\n    QualifiedResearchWorkerSessionError\n):\n    pass\n\n\ndef _aware_utc(value: datetime, field_name: str) -> datetime:\n    if (\n        not isinstance(value, datetime)\n        or value.tzinfo is None\n        or value.utcoffset() is None\n    ):\n        raise QualifiedResearchWorkerSessionInvariantError(\n            f"{field_name} must be timezone-aware."\n        )\n    return value.astimezone(timezone.utc)\n\n\ndef _canonical(value: Any) -> Any:\n    if is_dataclass(value):\n        return _canonical(asdict(value))\n    if isinstance(value, Mapping):\n        return {str(k): _canonical(v) for k, v in value.items()}\n    if isinstance(value, (list, tuple)):\n        return [_canonical(v) for v in value]\n    if isinstance(value, datetime):\n        return _aware_utc(value, "datetime").isoformat()\n    return value\n\n\ndef stable_hash(value: Any) -> str:\n    encoded = json.dumps(\n        _canonical(value),\n        sort_keys=True,\n        separators=(",", ":"),\n        ensure_ascii=False,\n        allow_nan=False,\n    ).encode("utf-8")\n    return hashlib.sha256(encoded).hexdigest()\n\n\ndef _freeze(value: Mapping[str, Any]) -> Mapping[str, Any]:\n    return MappingProxyType(dict(value))\n\n\ndef _valid_hash(value: Any) -> bool:\n    if not isinstance(value, str) or len(value) != 64:\n        return False\n    try:\n        int(value, 16)\n    except ValueError:\n        return False\n    return True\n\n\ndef _atomic_write(path: Path, payload: Mapping[str, Any]) -> None:\n    path.parent.mkdir(parents=True, exist_ok=True)\n    rendered = (\n        json.dumps(\n            _canonical(payload),\n            sort_keys=True,\n            indent=2,\n            ensure_ascii=False,\n        )\n        + "\\n"\n    )\n    handle = tempfile.NamedTemporaryFile(\n        mode="w",\n        encoding="utf-8",\n        newline="\\n",\n        delete=False,\n        dir=str(path.parent),\n        prefix=f".{path.name}.",\n        suffix=".tmp",\n    )\n    temporary = Path(handle.name)\n    try:\n        with handle:\n            handle.write(rendered)\n            handle.flush()\n            os.fsync(handle.fileno())\n        os.replace(temporary, path)\n    finally:\n        if temporary.exists():\n            temporary.unlink()\n\n\ndef _session_id(source_activation_hash: str, worker_id: str) -> str:\n    digest = stable_hash(\n        {\n            "source_activation_hash": source_activation_hash,\n            "worker_id": worker_id,\n            "session_policy_id": SESSION_POLICY_ID,\n        }\n    )\n    return f"oia023-session-{digest[:32]}"\n\n\n@dataclass(frozen=True)\nclass OracleQualifiedResearchWorkerSessionEntry:\n    session_sequence: int\n    activation_sequence: int\n    claim_sequence: int\n    dispatch_sequence: int\n    batch_number: int\n    batch_position: int\n    work_item_id: str\n    queue_position: int\n    source_rank: int\n    dimension: str\n    key: str\n    tier: str\n    priority_score: str\n    research_objective: str\n    required_operations: tuple[str, ...]\n    prohibited_operations: tuple[str, ...]\n    completion_requirements: tuple[str, ...]\n    session_entry_status: str\n    ranking_policy_id: str\n    tier_policy_id: str\n    queue_policy_id: str\n    work_item_policy_id: str\n    dispatch_policy_id: str\n    claim_policy_id: str\n    activation_policy_id: str\n    session_policy_id: str\n    source_eligibility_decision_hash: str\n    source_ranking_record_hash: str\n    source_tier_record_hash: str\n    source_queue_record_hash: str\n    source_work_item_hash: str\n    source_dispatch_entry_hash: str\n    source_claim_entry_hash: str\n    source_activation_entry_hash: str\n    session_entry_hash: str\n\n    def to_dict(self) -> Mapping[str, Any]:\n        return _freeze(_canonical(asdict(self)))\n\n\n@dataclass(frozen=True)\nclass OracleQualifiedResearchWorkerSessionManifest:\n    schema_version: str\n    engine_id: str\n    generated_at: datetime\n    session_id: str\n    session_status: str\n    worker_id: str\n    activation_directory: str\n    session_directory: str\n    source_activation_id: str\n    source_claim_id: str\n    manifest_id: str\n    selected_batch_id: str\n    selected_batch_number: int\n    session_entry_count: int\n    ranking_policy_id: str\n    tier_policy_id: str\n    queue_policy_id: str\n    work_item_policy_id: str\n    dispatch_policy_id: str\n    claim_policy_id: str\n    activation_policy_id: str\n    session_policy_id: str\n    entries: tuple[OracleQualifiedResearchWorkerSessionEntry, ...]\n    source_activation_hash: str\n    source_claim_hash: str\n    source_manifest_hash: str\n    source_batch_hash: str\n    read_only_corpus: bool\n    research_execution_allowed: bool\n    execution_allowed: bool\n    alerts_allowed: bool\n    qseries_handoff_allowed: bool\n    signals_allowed: bool\n    trading_recommendations_allowed: bool\n    source_mutation_allowed: bool\n    market_order_creation_allowed: bool\n    funds_movement_allowed: bool\n    portfolio_mutation_allowed: bool\n    session_artifact_persistence_allowed: bool\n    session_hash: str\n\n    def to_dict(self) -> Mapping[str, Any]:\n        return _freeze(_canonical(asdict(self)))\n\n\nclass OracleQualifiedResearchWorkerSessionManifestBuilder:\n    def __init__(\n        self,\n        *,\n        activation_directory: Path | str = DEFAULT_ACTIVATION_DIRECTORY,\n        session_directory: Path | str = DEFAULT_SESSION_DIRECTORY,\n    ) -> None:\n        self._activation_directory = Path(activation_directory)\n        self._session_directory = Path(session_directory)\n\n    def _load_activation(self) -> dict[str, Any]:\n        path = self._activation_directory / "current.json"\n        if not path.exists():\n            raise QualifiedResearchWorkerSessionInvariantError(\n                f"OIA-022 current activation is missing: {path}"\n            )\n        try:\n            payload = json.loads(path.read_text(encoding="utf-8"))\n        except json.JSONDecodeError as exc:\n            raise QualifiedResearchWorkerSessionInvariantError(\n                f"OIA-022 current activation is invalid JSON: {path}"\n            ) from exc\n        if not isinstance(payload, dict):\n            raise QualifiedResearchWorkerSessionInvariantError(\n                "OIA-022 activation must be a JSON object."\n            )\n\n        activation_hash = payload.pop("activation_hash", None)\n\n        expected = {\n            "schema_version": "OIA-022",\n            "engine_id": "OIA-022",\n            "activation_status": ACTIVATION_READY,\n            "ranking_policy_id": RANKING_POLICY_ID,\n            "tier_policy_id": TIER_POLICY_ID,\n            "queue_policy_id": QUEUE_POLICY_ID,\n            "work_item_policy_id": WORK_ITEM_POLICY_ID,\n            "dispatch_policy_id": DISPATCH_POLICY_ID,\n            "claim_policy_id": CLAIM_POLICY_ID,\n            "activation_policy_id": ACTIVATION_POLICY_ID,\n        }\n        for field_name, expected_value in expected.items():\n            if payload.get(field_name) != expected_value:\n                raise QualifiedResearchWorkerSessionInvariantError(\n                    f"OIA-022 identity mismatch: {field_name}."\n                )\n\n        if activation_hash != activation_stable_hash(payload):\n            raise QualifiedResearchWorkerSessionInvariantError(\n                "OIA-022 activation hash verification failed."\n            )\n        if not _valid_hash(activation_hash):\n            raise QualifiedResearchWorkerSessionInvariantError(\n                "OIA-022 activation hash is malformed."\n            )\n\n        if payload.get("read_only_corpus") is not True:\n            raise QualifiedResearchWorkerSessionInvariantError(\n                "OIA-022 read-only corpus invariant failed."\n            )\n\n        for field_name in (\n            "research_execution_allowed",\n            "execution_allowed",\n            "alerts_allowed",\n            "qseries_handoff_allowed",\n            "signals_allowed",\n            "trading_recommendations_allowed",\n            "source_mutation_allowed",\n            "market_order_creation_allowed",\n            "funds_movement_allowed",\n            "portfolio_mutation_allowed",\n        ):\n            if payload.get(field_name) is not False:\n                raise QualifiedResearchWorkerSessionInvariantError(\n                    f"OIA-022 safety boundary mismatch: {field_name}."\n                )\n\n        entries = payload.get("entries")\n        if not isinstance(entries, list) or not entries:\n            raise QualifiedResearchWorkerSessionInvariantError(\n                "OIA-022 activation entries must be a non-empty list."\n            )\n        if int(payload.get("activated_entry_count", -1)) != len(entries):\n            raise QualifiedResearchWorkerSessionInvariantError(\n                "OIA-022 activated entry count mismatch."\n            )\n\n        verified: list[dict[str, Any]] = []\n        previous_dispatch: int | None = None\n        seen_work_items: set[str] = set()\n        seen_hashes: set[str] = set()\n\n        for index, raw in enumerate(entries, start=1):\n            if not isinstance(raw, dict):\n                raise QualifiedResearchWorkerSessionInvariantError(\n                    f"OIA-022 activation entry {index} must be an object."\n                )\n            entry = dict(raw)\n            entry_hash = entry.pop("activation_entry_hash", None)\n            if entry_hash != activation_stable_hash(entry):\n                raise QualifiedResearchWorkerSessionInvariantError(\n                    f"OIA-022 activation-entry hash failed at index {index}."\n                )\n            if not _valid_hash(entry_hash):\n                raise QualifiedResearchWorkerSessionInvariantError(\n                    "OIA-022 activation-entry hash is malformed."\n                )\n            if int(entry.get("activation_sequence", -1)) != index:\n                raise QualifiedResearchWorkerSessionInvariantError(\n                    "OIA-022 activation sequences must be contiguous."\n                )\n            if entry.get("activation_status") != ENTRY_ACTIVATED:\n                raise QualifiedResearchWorkerSessionInvariantError(\n                    "OIA-022 entry is not activated."\n                )\n\n            dispatch_sequence = int(entry.get("dispatch_sequence", -1))\n            if (\n                previous_dispatch is not None\n                and dispatch_sequence != previous_dispatch + 1\n            ):\n                raise QualifiedResearchWorkerSessionInvariantError(\n                    "OIA-022 dispatch sequence is not contiguous."\n                )\n            previous_dispatch = dispatch_sequence\n\n            work_item_id = str(entry.get("work_item_id", ""))\n            if not work_item_id.startswith("oia019-"):\n                raise QualifiedResearchWorkerSessionInvariantError(\n                    "OIA-022 work-item ID is malformed."\n                )\n            if work_item_id in seen_work_items or entry_hash in seen_hashes:\n                raise QualifiedResearchWorkerSessionInvariantError(\n                    "Duplicate OIA-022 activation lineage."\n                )\n\n            for field_name, expected_value in (\n                ("ranking_policy_id", RANKING_POLICY_ID),\n                ("tier_policy_id", TIER_POLICY_ID),\n                ("queue_policy_id", QUEUE_POLICY_ID),\n                ("work_item_policy_id", WORK_ITEM_POLICY_ID),\n                ("dispatch_policy_id", DISPATCH_POLICY_ID),\n                ("claim_policy_id", CLAIM_POLICY_ID),\n                ("activation_policy_id", ACTIVATION_POLICY_ID),\n            ):\n                if entry.get(field_name) != expected_value:\n                    raise QualifiedResearchWorkerSessionInvariantError(\n                        f"OIA-022 entry policy mismatch: {field_name}."\n                    )\n\n            for field_name in (\n                "source_eligibility_decision_hash",\n                "source_ranking_record_hash",\n                "source_tier_record_hash",\n                "source_queue_record_hash",\n                "source_work_item_hash",\n                "source_dispatch_entry_hash",\n                "source_claim_entry_hash",\n            ):\n                if not _valid_hash(entry.get(field_name)):\n                    raise QualifiedResearchWorkerSessionInvariantError(\n                        f"OIA-022 {field_name} is malformed."\n                    )\n\n            for field_name in (\n                "required_operations",\n                "prohibited_operations",\n                "completion_requirements",\n            ):\n                value = entry.get(field_name)\n                if not isinstance(value, list) or not value:\n                    raise QualifiedResearchWorkerSessionInvariantError(\n                        f"OIA-022 {field_name} must be a non-empty list."\n                    )\n\n            required_prohibitions = {\n                "create_trading_signal",\n                "create_trading_recommendation",\n                "publish_operator_alert",\n                "handoff_to_qseries_execution",\n                "create_market_order",\n                "move_funds",\n                "mutate_portfolio",\n                "mutate_source_corpus",\n            }\n            if not required_prohibitions.issubset(\n                set(entry["prohibited_operations"])\n            ):\n                raise QualifiedResearchWorkerSessionInvariantError(\n                    "OIA-022 prohibited-operation boundary is incomplete."\n                )\n\n            entry["activation_entry_hash"] = entry_hash\n            verified.append(entry)\n            seen_work_items.add(work_item_id)\n            seen_hashes.add(entry_hash)\n\n        payload["entries"] = verified\n        payload["activation_hash"] = activation_hash\n        return payload\n\n    def build(\n        self,\n        *,\n        generated_at: datetime | None = None,\n        persist: bool = True,\n    ) -> OracleQualifiedResearchWorkerSessionManifest:\n        generated_at = _aware_utc(\n            generated_at or datetime.now(timezone.utc),\n            "generated_at",\n        )\n        activation = self._load_activation()\n        source_activation_hash = str(activation["activation_hash"])\n        worker_id = str(activation["worker_id"])\n        session_id = _session_id(source_activation_hash, worker_id)\n\n        entries: list[OracleQualifiedResearchWorkerSessionEntry] = []\n        for sequence, source in enumerate(activation["entries"], start=1):\n            body = {\n                "session_sequence": sequence,\n                "activation_sequence": int(source["activation_sequence"]),\n                "claim_sequence": int(source["claim_sequence"]),\n                "dispatch_sequence": int(source["dispatch_sequence"]),\n                "batch_number": int(source["batch_number"]),\n                "batch_position": int(source["batch_position"]),\n                "work_item_id": str(source["work_item_id"]),\n                "queue_position": int(source["queue_position"]),\n                "source_rank": int(source["source_rank"]),\n                "dimension": str(source["dimension"]),\n                "key": str(source["key"]),\n                "tier": str(source["tier"]),\n                "priority_score": str(source["priority_score"]),\n                "research_objective": str(source["research_objective"]),\n                "required_operations": tuple(source["required_operations"]),\n                "prohibited_operations": tuple(source["prohibited_operations"]),\n                "completion_requirements": tuple(\n                    source["completion_requirements"]\n                ),\n                "session_entry_status": SESSION_ENTRY_READY,\n                "ranking_policy_id": RANKING_POLICY_ID,\n                "tier_policy_id": TIER_POLICY_ID,\n                "queue_policy_id": QUEUE_POLICY_ID,\n                "work_item_policy_id": WORK_ITEM_POLICY_ID,\n                "dispatch_policy_id": DISPATCH_POLICY_ID,\n                "claim_policy_id": CLAIM_POLICY_ID,\n                "activation_policy_id": ACTIVATION_POLICY_ID,\n                "session_policy_id": SESSION_POLICY_ID,\n                "source_eligibility_decision_hash": str(\n                    source["source_eligibility_decision_hash"]\n                ),\n                "source_ranking_record_hash": str(\n                    source["source_ranking_record_hash"]\n                ),\n                "source_tier_record_hash": str(\n                    source["source_tier_record_hash"]\n                ),\n                "source_queue_record_hash": str(\n                    source["source_queue_record_hash"]\n                ),\n                "source_work_item_hash": str(\n                    source["source_work_item_hash"]\n                ),\n                "source_dispatch_entry_hash": str(\n                    source["source_dispatch_entry_hash"]\n                ),\n                "source_claim_entry_hash": str(\n                    source["source_claim_entry_hash"]\n                ),\n                "source_activation_entry_hash": str(\n                    source["activation_entry_hash"]\n                ),\n            }\n            entries.append(\n                OracleQualifiedResearchWorkerSessionEntry(\n                    **body,\n                    session_entry_hash=stable_hash(body),\n                )\n            )\n\n        body = {\n            "schema_version": SCHEMA_VERSION,\n            "engine_id": ENGINE_ID,\n            "generated_at": generated_at,\n            "session_id": session_id,\n            "session_status": SESSION_READY,\n            "worker_id": worker_id,\n            "activation_directory": str(self._activation_directory),\n            "session_directory": str(self._session_directory),\n            "source_activation_id": str(activation["activation_id"]),\n            "source_claim_id": str(activation["source_claim_id"]),\n            "manifest_id": str(activation["manifest_id"]),\n            "selected_batch_id": str(activation["selected_batch_id"]),\n            "selected_batch_number": int(\n                activation["selected_batch_number"]\n            ),\n            "session_entry_count": len(entries),\n            "ranking_policy_id": RANKING_POLICY_ID,\n            "tier_policy_id": TIER_POLICY_ID,\n            "queue_policy_id": QUEUE_POLICY_ID,\n            "work_item_policy_id": WORK_ITEM_POLICY_ID,\n            "dispatch_policy_id": DISPATCH_POLICY_ID,\n            "claim_policy_id": CLAIM_POLICY_ID,\n            "activation_policy_id": ACTIVATION_POLICY_ID,\n            "session_policy_id": SESSION_POLICY_ID,\n            "entries": tuple(entries),\n            "source_activation_hash": source_activation_hash,\n            "source_claim_hash": str(activation["source_claim_hash"]),\n            "source_manifest_hash": str(activation["source_manifest_hash"]),\n            "source_batch_hash": str(activation["source_batch_hash"]),\n            "read_only_corpus": READ_ONLY_CORPUS,\n            "research_execution_allowed": RESEARCH_EXECUTION_ALLOWED,\n            "execution_allowed": EXECUTION_ALLOWED,\n            "alerts_allowed": ALERTS_ALLOWED,\n            "qseries_handoff_allowed": QSERIES_HANDOFF_ALLOWED,\n            "signals_allowed": SIGNALS_ALLOWED,\n            "trading_recommendations_allowed": TRADING_RECOMMENDATIONS_ALLOWED,\n            "source_mutation_allowed": SOURCE_MUTATION_ALLOWED,\n            "market_order_creation_allowed": MARKET_ORDER_CREATION_ALLOWED,\n            "funds_movement_allowed": FUNDS_MOVEMENT_ALLOWED,\n            "portfolio_mutation_allowed": PORTFOLIO_MUTATION_ALLOWED,\n            "session_artifact_persistence_allowed": (\n                SESSION_ARTIFACT_PERSISTENCE_ALLOWED\n            ),\n        }\n        session = OracleQualifiedResearchWorkerSessionManifest(\n            **body,\n            session_hash=stable_hash(body),\n        )\n\n        if persist:\n            payload = dict(session.to_dict())\n            _atomic_write(self._session_directory / "current.json", payload)\n            _atomic_write(\n                self._session_directory\n                / "sessions"\n                / f"{session.session_id}-{session.session_hash}.json",\n                payload,\n            )\n            _atomic_write(\n                self._session_directory\n                / "workers"\n                / worker_id\n                / f"{session.session_id}.json",\n                payload,\n            )\n        return session\n\n\ndef format_session(\n    session: OracleQualifiedResearchWorkerSessionManifest,\n) -> str:\n    lines = [\n        "=" * 154,\n        "ORACLE QUALIFIED RESEARCH WORKER SESSION MANIFEST",\n        "=" * 154,\n        f"Generated at:   {session.generated_at.isoformat()}",\n        f"Session ID:     {session.session_id}",\n        f"Session status: {session.session_status}",\n        f"Worker ID:      {session.worker_id}",\n        f"Activation ID:  {session.source_activation_id}",\n        f"Session entries:{session.session_entry_count}",\n        "-" * 154,\n    ]\n    for entry in session.entries:\n        lines.append(\n            f"{entry.session_sequence:>4} | "\n            f"dispatch={entry.dispatch_sequence:>4} | "\n            f"queue={entry.queue_position:>4} | "\n            f"tier={entry.tier:<10} | "\n            f"{entry.dimension}:{entry.key} | "\n            f"{entry.session_entry_status}"\n        )\n    lines.extend(\n        [\n            "-" * 154,\n            f"Session hash: {session.session_hash}",\n            (\n                "SESSION MATERIALIZATION ONLY — NO RESEARCH EXECUTION, "\n                "SIGNALS, ALERTS, RECOMMENDATIONS, QSERIES HANDOFFS, "\n                "ORDERS, FUNDS MOVEMENT, PORTFOLIO MUTATION, "\n                "OR SOURCE MUTATION"\n            ),\n        ]\n    )\n    return "\\n".join(lines)\n\n\ndef main(argv: list[str] | None = None) -> int:\n    parser = argparse.ArgumentParser(\n        description="OIA-023 qualified research worker session manifest"\n    )\n    parser.add_argument(\n        "--activation-directory",\n        default=str(DEFAULT_ACTIVATION_DIRECTORY),\n    )\n    parser.add_argument(\n        "--session-directory",\n        default=str(DEFAULT_SESSION_DIRECTORY),\n    )\n    parser.add_argument("--no-persist", action="store_true")\n    args = parser.parse_args(argv)\n    session = OracleQualifiedResearchWorkerSessionManifestBuilder(\n        activation_directory=args.activation_directory,\n        session_directory=args.session_directory,\n    ).build(persist=not args.no_persist)\n    print(format_session(session))\n    return 0\n\n\nif __name__ == "__main__":\n    raise SystemExit(main())\n'

TEST_SOURCE = 'from __future__ import annotations\n\nimport json\nfrom datetime import datetime, timezone\nfrom pathlib import Path\nfrom tempfile import TemporaryDirectory\n\nfrom qseries_v2.oracle_intelligence.analytics.oracle_qualified_research_priority_ranking_engine import RANKING_POLICY_ID\nfrom qseries_v2.oracle_intelligence.analytics.oracle_qualified_research_priority_tier_assignment_gate import TIER_POLICY_ID\nfrom qseries_v2.oracle_intelligence.analytics.oracle_qualified_research_queue_admission_gate import QUEUE_POLICY_ID\nfrom qseries_v2.oracle_intelligence.analytics.oracle_qualified_research_work_item_materialization_engine import WORK_ITEM_POLICY_ID\nfrom qseries_v2.oracle_intelligence.analytics.oracle_qualified_research_dispatch_manifest_builder import DISPATCH_POLICY_ID\nfrom qseries_v2.oracle_intelligence.analytics.oracle_qualified_research_dispatch_claim_gate import CLAIM_POLICY_ID\nfrom qseries_v2.oracle_intelligence.analytics.oracle_qualified_research_claim_activation_gate import (\n    ACTIVATION_POLICY_ID,\n    ACTIVATION_READY,\n    ENTRY_ACTIVATED,\n    stable_hash as activation_hash,\n)\nfrom qseries_v2.oracle_intelligence.analytics.oracle_qualified_research_worker_session_manifest_builder import (\n    SESSION_POLICY_ID,\n    SESSION_READY,\n    SESSION_ENTRY_READY,\n    OracleQualifiedResearchWorkerSessionManifestBuilder,\n    QualifiedResearchWorkerSessionInvariantError,\n    format_session,\n    stable_hash,\n)\n\nNOW = datetime(2026, 7, 21, 11, 0, 0, tzinfo=timezone.utc)\n\n\ndef make_entry(index: int) -> dict:\n    body = {\n        "activation_sequence": index,\n        "claim_sequence": index,\n        "dispatch_sequence": index + 4,\n        "batch_number": 3,\n        "batch_position": index,\n        "work_item_id": f"oia019-{index:032x}",\n        "queue_position": index + 4,\n        "source_rank": index + 4,\n        "dimension": "candidate_family_horizon",\n        "key": f"candidate-{index}|1800",\n        "tier": "tier_2",\n        "priority_score": f"{60-index}.00000000",\n        "research_objective": (\n            "evaluate_qualified_component_with_additional_read_only_evidence"\n        ),\n        "required_operations": [\n            "load_verified_source_lineage",\n            "read_additional_canonical_market_evidence",\n        ],\n        "prohibited_operations": [\n            "create_trading_signal",\n            "create_trading_recommendation",\n            "publish_operator_alert",\n            "handoff_to_qseries_execution",\n            "create_market_order",\n            "move_funds",\n            "mutate_portfolio",\n            "mutate_source_corpus",\n        ],\n        "completion_requirements": [\n            "source_lineage_hashes_verified",\n            "research_output_deterministically_hashed",\n        ],\n        "activation_status": ENTRY_ACTIVATED,\n        "ranking_policy_id": RANKING_POLICY_ID,\n        "tier_policy_id": TIER_POLICY_ID,\n        "queue_policy_id": QUEUE_POLICY_ID,\n        "work_item_policy_id": WORK_ITEM_POLICY_ID,\n        "dispatch_policy_id": DISPATCH_POLICY_ID,\n        "claim_policy_id": CLAIM_POLICY_ID,\n        "activation_policy_id": ACTIVATION_POLICY_ID,\n        "source_eligibility_decision_hash": f"{index:064x}",\n        "source_ranking_record_hash": f"{index+100:064x}",\n        "source_tier_record_hash": f"{index+200:064x}",\n        "source_queue_record_hash": f"{index+300:064x}",\n        "source_work_item_hash": f"{index+400:064x}",\n        "source_dispatch_entry_hash": f"{index+500:064x}",\n        "source_claim_entry_hash": f"{index+600:064x}",\n    }\n    return {**body, "activation_entry_hash": activation_hash(body)}\n\n\ndef write_activation(directory: Path) -> dict:\n    entries = [make_entry(1), make_entry(2)]\n    body = {\n        "schema_version": "OIA-022",\n        "engine_id": "OIA-022",\n        "generated_at": NOW,\n        "activation_id": "oia022-activation-" + "a" * 32,\n        "activation_status": ACTIVATION_READY,\n        "worker_id": "oracle-research-worker-01",\n        "claim_directory": "claims",\n        "activation_directory": str(directory),\n        "source_claim_id": "oia021-claim-" + "b" * 32,\n        "manifest_id": "oia020-manifest-" + "c" * 32,\n        "selected_batch_id": "oia020-batch-" + "d" * 32,\n        "selected_batch_number": 3,\n        "activated_entry_count": 2,\n        "ranking_policy_id": RANKING_POLICY_ID,\n        "tier_policy_id": TIER_POLICY_ID,\n        "queue_policy_id": QUEUE_POLICY_ID,\n        "work_item_policy_id": WORK_ITEM_POLICY_ID,\n        "dispatch_policy_id": DISPATCH_POLICY_ID,\n        "claim_policy_id": CLAIM_POLICY_ID,\n        "activation_policy_id": ACTIVATION_POLICY_ID,\n        "entries": entries,\n        "source_claim_hash": "e" * 64,\n        "source_manifest_hash": "f" * 64,\n        "source_batch_hash": "1" * 64,\n        "read_only_corpus": True,\n        "research_execution_allowed": False,\n        "execution_allowed": False,\n        "alerts_allowed": False,\n        "qseries_handoff_allowed": False,\n        "signals_allowed": False,\n        "trading_recommendations_allowed": False,\n        "source_mutation_allowed": False,\n        "market_order_creation_allowed": False,\n        "funds_movement_allowed": False,\n        "portfolio_mutation_allowed": False,\n        "activation_artifact_persistence_allowed": True,\n    }\n    payload = {**body, "activation_hash": activation_hash(body)}\n    directory.mkdir(parents=True, exist_ok=True)\n    (directory / "current.json").write_text(\n        json.dumps(\n            payload,\n            sort_keys=True,\n            indent=2,\n            default=lambda value: value.isoformat(),\n        ) + "\\n",\n        encoding="utf-8",\n    )\n    return payload\n\n\ndef run_test() -> None:\n    with TemporaryDirectory() as temporary:\n        root = Path(temporary)\n        activation_directory = root / "activations"\n        session_directory = root / "sessions"\n        source = write_activation(activation_directory)\n\n        builder = OracleQualifiedResearchWorkerSessionManifestBuilder(\n            activation_directory=activation_directory,\n            session_directory=session_directory,\n        )\n        session = builder.build(generated_at=NOW, persist=True)\n\n        assert session.schema_version == "OIA-023"\n        assert session.engine_id == "OIA-023"\n        assert session.session_status == SESSION_READY\n        assert session.session_policy_id == SESSION_POLICY_ID\n        assert session.session_entry_count == 2\n        assert session.source_activation_hash == source["activation_hash"]\n        assert [e.session_sequence for e in session.entries] == [1, 2]\n        assert [e.dispatch_sequence for e in session.entries] == [5, 6]\n        assert all(\n            e.session_entry_status == SESSION_ENTRY_READY\n            for e in session.entries\n        )\n\n        for entry in session.entries:\n            payload = dict(entry.to_dict())\n            digest = payload.pop("session_entry_hash")\n            assert digest == stable_hash(payload)\n\n        payload = dict(session.to_dict())\n        digest = payload.pop("session_hash")\n        assert digest == stable_hash(payload)\n        assert session.read_only_corpus\n        assert not session.research_execution_allowed\n        assert not session.execution_allowed\n        assert not session.qseries_handoff_allowed\n        assert not session.market_order_creation_allowed\n        assert not session.funds_movement_allowed\n        assert not session.portfolio_mutation_allowed\n\n        current = session_directory / "current.json"\n        immutable = (\n            session_directory\n            / "sessions"\n            / f"{session.session_id}-{session.session_hash}.json"\n        )\n        assert current.exists()\n        assert immutable.exists()\n        before = current.read_bytes()\n\n        replay = builder.build(generated_at=NOW, persist=True)\n        assert replay.session_id == session.session_id\n        assert replay.session_hash == session.session_hash\n        assert current.read_bytes() == before\n\n        rendered = format_session(session)\n        assert "ORACLE QUALIFIED RESEARCH WORKER SESSION MANIFEST" in rendered\n        assert "NO RESEARCH EXECUTION" in rendered\n\n        tampered = json.loads(\n            (activation_directory / "current.json").read_text(\n                encoding="utf-8"\n            )\n        )\n        tampered["entries"][0]["priority_score"] = "0.00000000"\n        (activation_directory / "current.json").write_text(\n            json.dumps(tampered, sort_keys=True, indent=2) + "\\n",\n            encoding="utf-8",\n        )\n\n        try:\n            builder.build(generated_at=NOW, persist=False)\n        except QualifiedResearchWorkerSessionInvariantError:\n            pass\n        else:\n            raise AssertionError("Tampered OIA-022 activation was not rejected.")\n\n    print(\n        "[PASS] OIA-023 Oracle Qualified Research "\n        "Worker Session Manifest Builder"\n    )\n\n\nif __name__ == "__main__":\n    run_test()\n'

INIT_IMPORT_BLOCK = 'from .oracle_qualified_research_worker_session_manifest_builder import (\n    SESSION_ENTRY_READY,\n    SESSION_POLICY_ID,\n    SESSION_READY,\n    OracleQualifiedResearchWorkerSessionEntry,\n    OracleQualifiedResearchWorkerSessionManifest,\n    OracleQualifiedResearchWorkerSessionManifestBuilder,\n)\n'

INIT_EXPORTS = (
    "SESSION_ENTRY_READY",
    "SESSION_POLICY_ID",
    "SESSION_READY",
    "OracleQualifiedResearchWorkerSessionEntry",
    "OracleQualifiedResearchWorkerSessionManifest",
    "OracleQualifiedResearchWorkerSessionManifestBuilder",
)


def write_full_replacement(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")
    print(f"[OK] FULL REPLACEMENT: {path.resolve()}")


def verify_oia_022_contract(path: Path) -> None:
    if not path.exists():
        raise SystemExit(
            "[FAIL] OIA-022 production module is missing. "
            "Install and pass OIA-022 first."
        )

    text = path.read_text(encoding="utf-8")

    required = (
        'SCHEMA_VERSION = "OIA-022"',
        'ENGINE_ID = "OIA-022"',
        "ACTIVATION_POLICY_ID",
        "oracle.qualified-research-claim-activation.v1",
        'ACTIVATION_READY = "activation_ready"',
        'ENTRY_ACTIVATED = "entry_activated"',
        "DEFAULT_ACTIVATION_DIRECTORY",
        "class OracleQualifiedResearchClaimActivationEntry:",
        "class OracleQualifiedResearchClaimActivation:",
        "class OracleQualifiedResearchClaimActivationGate:",
        "activation_sequence",
        "source_claim_hash",
        "source_manifest_hash",
        "source_batch_hash",
        "activation_entry_hash",
        "activation_hash",
        "research_execution_allowed",
        "qseries_handoff_allowed",
        "activation_artifact_persistence_allowed",
    )

    missing = [
        token
        for token in required
        if token not in text
    ]

    if missing:
        raise SystemExit(
            f"[FAIL] Actual OIA-022 production contract mismatch: {missing}"
        )


def update_package_initializer(path: Path) -> None:
    if not path.exists():
        raise SystemExit(
            f"[FAIL] Analytics package initializer is missing: {path}"
        )

    original = path.read_text(encoding="utf-8")
    updated = original

    marker = (
        "from "
        ".oracle_qualified_research_worker_session_"
        "manifest_builder import"
    )

    if marker not in updated:
        updated = (
            updated.rstrip()
            + "\n\n"
            + INIT_IMPORT_BLOCK.strip()
            + "\n"
        )

    if "__all__" in updated:
        missing_exports = [
            name
            for name in INIT_EXPORTS
            if (
                f'"{name}"' not in updated
                and f"'{name}'" not in updated
            )
        ]

        if missing_exports:
            export_lines = "\n".join(
                f'    "{name}",'
                for name in missing_exports
            )

            updated = (
                updated.rstrip()
                + "\n\n__all__ = [\n"
                + export_lines
                + "\n] + __all__\n"
            )

    if updated == original:
        print(
            "[OK] PACKAGE EXPORTS ALREADY PRESENT: "
            f"{path.resolve()}"
        )
        return

    path.write_text(
        updated,
        encoding="utf-8",
        newline="\n",
    )

    print(
        f"[OK] PACKAGE EXPORT UPDATE: {path.resolve()}"
    )


def main() -> int:
    root = Path.cwd()

    analytics = (
        root
        / "qseries_v2"
        / "oracle_intelligence"
        / "analytics"
    )

    dependency = (
        analytics
        / "oracle_qualified_research_claim_activation_gate.py"
    )

    production = (
        analytics
        / (
            "oracle_qualified_research_worker_"
            "session_manifest_builder.py"
        )
    )

    test = (
        root
        / (
            "test_oia_023_oracle_qualified_research_"
            "worker_session_manifest_builder.py"
        )
    )

    initializer = analytics / "__init__.py"

    print("========================================")
    print(" OIA-023 INSTALLER")
    print(" QUALIFIED RESEARCH WORKER")
    print(" SESSION MANIFEST BUILDER")
    print("========================================")

    verify_oia_022_contract(dependency)

    print(
        "[OK] Actual OIA-022 claim activation "
        "contract verified"
    )

    write_full_replacement(
        production,
        MODULE_SOURCE,
    )

    write_full_replacement(
        test,
        TEST_SOURCE,
    )

    update_package_initializer(
        initializer
    )

    ast.parse(
        MODULE_SOURCE,
        filename=str(production),
    )

    ast.parse(
        TEST_SOURCE,
        filename=str(test),
    )

    ast.parse(
        initializer.read_text(
            encoding="utf-8"
        ),
        filename=str(initializer),
    )

    print(
        "[OK] OIA-023 production, package, "
        "and test syntax verified"
    )

    completed = subprocess.run(
        [
            sys.executable,
            str(test),
        ],
        cwd=root,
        check=False,
    )

    if completed.returncode != 0:
        raise SystemExit(
            completed.returncode
        )

    print(
        "[OK] OIA-023 test executed successfully"
    )

    print(
        "[DONE] OIA-023 Oracle Qualified Research "
        "Worker Session Manifest Builder installed"
    )

    print()

    print(
        "Build the current research worker "
        "session manifest with:"
    )

    print(
        "python -m "
        "qseries_v2.oracle_intelligence.analytics."
        "oracle_qualified_research_worker_"
        "session_manifest_builder"
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )