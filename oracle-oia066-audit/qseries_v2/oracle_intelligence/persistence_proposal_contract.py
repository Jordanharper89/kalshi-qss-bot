from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from hashlib import sha256
from typing import Any, Dict, Mapping, Tuple


SCHEMA_VERSION = "ORP-001"
PROPOSAL_ID_PREFIX = "orp_"
VALID_EVENT_SEVERITIES = {"info", "warning", "error", "critical"}
VALID_RECOVERY_ACTIONS = {"cold_start", "resume", "resume_with_validation"}

_FORBIDDEN_KEYWORDS = (
    "insert into",
    "update ",
    "delete from",
    "create table",
    "create index",
    "drop table",
    "alter table",
    "pragma ",
    "sqlite3",
    "connect(",
    "commit(",
    "rollback(",
    "save_snapshot",
    "log_event",
    "persist",
    "write_text",
    "write_bytes",
    "open(",
    "mkdir",
    "unlink",
    "rmtree",
    "remove(",
    "replace(",
    "rename(",
)
_DATABASE_OR_RUNTIME_PATH = re.compile(
    r"(^|[\\/])runtime([\\/]|$)|(^|[\\/])qseries_v2[\\/]data[\\/]|"
    r"(^|[\\/])oracle[\\/]data[\\/]|\.(db|sqlite|sqlite3)$",
    re.IGNORECASE,
)
_MUTABLE_RUNTIME_TYPES = (bytearray, memoryview)
_JSON_SCALARS = (str, int, float, bool, type(None))


def stable_json(value: Any) -> str:
    return json.dumps(_to_json_value(value), sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def stable_hash(value: Any) -> str:
    return sha256(stable_json(value).encode("utf-8")).hexdigest()


def _freeze_json(value: Any) -> Any:
    if isinstance(value, Mapping):
        return tuple((str(key), _freeze_json(value[key])) for key in sorted(value, key=lambda item: str(item)))
    if isinstance(value, tuple):
        return tuple(_freeze_json(item) for item in value)
    if isinstance(value, list):
        return tuple(_freeze_json(item) for item in value)
    if isinstance(value, _JSON_SCALARS):
        return value
    return value


def _to_json_value(value: Any) -> Any:
    if isinstance(value, tuple):
        if all(isinstance(item, tuple) and len(item) == 2 and isinstance(item[0], str) for item in value):
            return {key: _to_json_value(item_value) for key, item_value in value}
        return [_to_json_value(item) for item in value]
    if isinstance(value, Mapping):
        return {str(key): _to_json_value(item_value) for key, item_value in value.items()}
    if isinstance(value, list):
        return [_to_json_value(item) for item in value]
    if isinstance(value, _JSON_SCALARS):
        return value
    raise TypeError(f"Value is not JSON serializable: {type(value).__name__}")


def _validate_payload_value(value: Any, path: str = "payload") -> None:
    if callable(value):
        raise ValueError(f"{path} contains callable value")
    if isinstance(value, _MUTABLE_RUNTIME_TYPES):
        raise ValueError(f"{path} contains mutable runtime handle")
    if isinstance(value, Mapping):
        for key, item_value in value.items():
            if not isinstance(key, str):
                raise ValueError(f"{path} contains non-string key")
            _validate_text(key, f"{path}.{key}")
            _validate_payload_value(item_value, f"{path}.{key}")
        return
    if isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            _validate_payload_value(item, f"{path}[{index}]")
        return
    if isinstance(value, str):
        _validate_text(value, path)
        return
    if isinstance(value, _JSON_SCALARS):
        return
    raise ValueError(f"{path} contains unsupported runtime object: {type(value).__name__}")


def _validate_text(value: str, path: str) -> None:
    lower = value.lower()
    if any(keyword in lower for keyword in _FORBIDDEN_KEYWORDS):
        raise ValueError(f"{path} contains SQL or persistence command")
    if _DATABASE_OR_RUNTIME_PATH.search(value):
        raise ValueError(f"{path} contains database or runtime write path")


def _proposal_id_payload(
    *,
    proposal_type: str,
    oracle_module_id: str,
    kind: str,
    payload_hash: str,
    source_runtime_id: str | None,
) -> Dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "proposal_type": proposal_type,
        "oracle_module_id": oracle_module_id,
        "kind": kind,
        "payload_hash": payload_hash,
        "source_runtime_id": source_runtime_id,
    }


def _proposal_hash_payload(data: Dict[str, Any]) -> Dict[str, Any]:
    return {key: value for key, value in data.items() if key != "proposal_hash"}


@dataclass(frozen=True)
class _ProposalBase:
    oracle_module_id: str
    payload: Mapping[str, Any]
    proposed_at: str
    source_runtime_id: str | None = None
    read_only: bool = True
    execution_allowed: bool = False
    qseries_authorization_required: bool = True
    replay_metadata: Mapping[str, Any] = field(default_factory=dict)
    schema_version: str = field(default=SCHEMA_VERSION, init=False)
    proposal_type: str = field(default="", init=False)
    payload_hash: str = field(default="", init=False)
    proposal_id: str = field(default="", init=False)
    proposal_hash: str = field(default="", init=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "payload", _freeze_json(self.payload))
        object.__setattr__(self, "replay_metadata", _freeze_json(self.replay_metadata))
        payload_hash = stable_hash(self.payload)
        object.__setattr__(self, "payload_hash", payload_hash)
        proposal_id = PROPOSAL_ID_PREFIX + stable_hash(
            _proposal_id_payload(
                proposal_type=self.proposal_type,
                oracle_module_id=self.oracle_module_id,
                kind=self._kind_for_id(),
                payload_hash=payload_hash,
                source_runtime_id=self.source_runtime_id,
            )
        )[:24]
        object.__setattr__(self, "proposal_id", proposal_id)
        proposal_hash = stable_hash(_proposal_hash_payload(self.to_dict(include_hash=False)))
        object.__setattr__(self, "proposal_hash", proposal_hash)

    def _kind_for_id(self) -> str:
        raise NotImplementedError

    def validate(self) -> bool:
        if self.schema_version != SCHEMA_VERSION:
            raise ValueError("schema_version must be ORP-001")
        if self.read_only is not True:
            raise ValueError("read_only must be True")
        if self.execution_allowed is not False:
            raise ValueError("execution_allowed must be False")
        if self.qseries_authorization_required is not True:
            raise ValueError("qseries_authorization_required must be True")
        if not self.oracle_module_id:
            raise ValueError("oracle_module_id is required")
        if not self.proposed_at:
            raise ValueError("proposed_at must be supplied by the caller")
        _validate_payload_value(self.payload)
        _validate_payload_value(self.replay_metadata, "replay_metadata")
        if self.payload_hash != stable_hash(self.payload):
            raise ValueError("payload_hash does not match payload")
        expected_id = PROPOSAL_ID_PREFIX + stable_hash(
            _proposal_id_payload(
                proposal_type=self.proposal_type,
                oracle_module_id=self.oracle_module_id,
                kind=self._kind_for_id(),
                payload_hash=self.payload_hash,
                source_runtime_id=self.source_runtime_id,
            )
        )[:24]
        if self.proposal_id != expected_id:
            raise ValueError("proposal_id does not match canonical fields")
        expected_hash = stable_hash(_proposal_hash_payload(self.to_dict(include_hash=False)))
        if self.proposal_hash != expected_hash:
            raise ValueError("proposal_hash does not match proposal")
        return True

    def to_dict(self, include_hash: bool = True) -> Dict[str, Any]:
        data = asdict(self)
        data["payload"] = _to_json_value(self.payload)
        data["replay_metadata"] = _to_json_value(self.replay_metadata)
        if not include_hash:
            data["proposal_hash"] = ""
        return data


@dataclass(frozen=True)
class OracleSnapshotPersistenceProposal(_ProposalBase):
    snapshot_type: str = ""
    proposal_type: str = field(default="snapshot", init=False)

    def _kind_for_id(self) -> str:
        return self.snapshot_type

    def validate(self) -> bool:
        super().validate()
        if not self.snapshot_type:
            raise ValueError("snapshot_type is required")
        _validate_text(self.snapshot_type, "snapshot_type")
        return True


@dataclass(frozen=True)
class OracleEventPersistenceProposal(_ProposalBase):
    event_type: str = ""
    severity: str = "info"
    proposal_type: str = field(default="event", init=False)

    def _kind_for_id(self) -> str:
        return self.event_type

    def validate(self) -> bool:
        super().validate()
        if not self.event_type:
            raise ValueError("event_type is required")
        if self.severity not in VALID_EVENT_SEVERITIES:
            raise ValueError("severity must be one of info, warning, error, critical")
        _validate_text(self.event_type, "event_type")
        return True


@dataclass(frozen=True)
class OracleRecoveryPersistenceProposal(_ProposalBase):
    recovery_action: str = "cold_start"
    safe_to_resume: bool = True
    warnings: Tuple[str, ...] = field(default_factory=tuple)
    steps: Tuple[str, ...] = field(default_factory=tuple)
    evidence: Mapping[str, Any] = field(default_factory=dict)
    proposal_type: str = field(default="recovery", init=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "warnings", tuple(str(item) for item in self.warnings))
        object.__setattr__(self, "steps", tuple(str(item) for item in self.steps))
        object.__setattr__(self, "evidence", _freeze_json(self.evidence))
        super().__post_init__()

    def _kind_for_id(self) -> str:
        return self.recovery_action

    def validate(self) -> bool:
        super().validate()
        if self.recovery_action not in VALID_RECOVERY_ACTIONS:
            raise ValueError("recovery_action must be cold_start, resume, or resume_with_validation")
        if not isinstance(self.safe_to_resume, bool):
            raise ValueError("safe_to_resume must be bool")
        _validate_payload_value(self.warnings, "warnings")
        _validate_payload_value(self.steps, "steps")
        _validate_payload_value(self.evidence, "evidence")
        return True

    def to_dict(self, include_hash: bool = True) -> Dict[str, Any]:
        data = super().to_dict(include_hash=include_hash)
        data["warnings"] = list(self.warnings)
        data["steps"] = list(self.steps)
        data["evidence"] = _to_json_value(self.evidence)
        return data


__all__ = [
    "SCHEMA_VERSION",
    "VALID_EVENT_SEVERITIES",
    "VALID_RECOVERY_ACTIONS",
    "OracleSnapshotPersistenceProposal",
    "OracleEventPersistenceProposal",
    "OracleRecoveryPersistenceProposal",
    "stable_json",
    "stable_hash",
]
