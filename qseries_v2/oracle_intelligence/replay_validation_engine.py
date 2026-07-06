"""
OI-156 — Oracle Replay Validation Engine

Read-only validation engine for Oracle Historical Replay output.

Purpose:
- Validate replay frames for institutional replay integrity.
- Confirm Oracle remains intelligence-only and read-only.
- Detect missing lineage, rank issues, execution violations, and replay quality gaps.

Oracle never executes trades, manages positions, or submits orders.
Execution ownership remains with Q Series.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
from typing import Any, Dict, List


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe_dict(value: Any) -> Dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _safe_list(value: Any) -> List[Any]:
    return value if isinstance(value, list) else []


def _num(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except Exception:
        return default


def _stable_text(value: Any) -> str:
    if isinstance(value, dict):
        return "{" + ",".join(f"{k}:{_stable_text(value[k])}" for k in sorted(value)) + "}"
    if isinstance(value, list):
        return "[" + ",".join(_stable_text(v) for v in value) + "]"
    return repr(value)


def _hash(value: Any, size: int = 24) -> str:
    return sha256(_stable_text(value).encode("utf-8")).hexdigest()[:size]


@dataclass
class ReplayValidationIssue:
    frame_id: str
    severity: str
    code: str
    message: str


@dataclass
class OracleReplayValidationEngine:
    name: str = "oracle_replay_validation_engine"
    version: str = "OI-156"
    read_only: bool = True
    execution_allowed: bool = False
    execution_owner: str = "Q Series"
    validation_schema_version: str = "replay_validation_v1"

    def _validate_frame(self, frame: Dict[str, Any], expected_rank: int) -> List[ReplayValidationIssue]:
        frame = _safe_dict(frame)
        frame_id = str(frame.get("replay_frame_id") or "unknown-frame")
        issues: List[ReplayValidationIssue] = []

        required = [
            "replay_frame_id",
            "replay_rank",
            "source_id",
            "source_type",
            "market",
            "replay_score",
            "replay_tier",
            "replay_status",
            "lineage_hash",
        ]

        for field in required:
            if frame.get(field) in (None, ""):
                issues.append(ReplayValidationIssue(
                    frame_id=frame_id,
                    severity="critical",
                    code="missing_required_field",
                    message=f"Replay frame missing required field: {field}",
                ))

        if frame.get("read_only") is not True:
            issues.append(ReplayValidationIssue(
                frame_id=frame_id,
                severity="critical",
                code="read_only_violation",
                message="Replay frame is not marked read_only=True.",
            ))

        if frame.get("execution_allowed") is not False:
            issues.append(ReplayValidationIssue(
                frame_id=frame_id,
                severity="critical",
                code="execution_violation",
                message="Replay frame allows execution. Oracle must remain read-only.",
            ))

        if frame.get("execution_owner") != "Q Series":
            issues.append(ReplayValidationIssue(
                frame_id=frame_id,
                severity="critical",
                code="execution_owner_violation",
                message="Replay frame execution_owner must be Q Series.",
            ))

        if int(_num(frame.get("replay_rank"), -1)) != expected_rank:
            issues.append(ReplayValidationIssue(
                frame_id=frame_id,
                severity="warning",
                code="rank_mismatch",
                message=f"Replay frame rank mismatch. Expected {expected_rank}.",
            ))

        score = _num(frame.get("replay_score"))
        if score < 0 or score > 100:
            issues.append(ReplayValidationIssue(
                frame_id=frame_id,
                severity="critical",
                code="score_out_of_bounds",
                message="Replay score must be between 0 and 100.",
            ))

        if not str(frame.get("lineage_hash") or "").strip():
            issues.append(ReplayValidationIssue(
                frame_id=frame_id,
                severity="critical",
                code="missing_lineage",
                message="Replay frame missing lineage hash.",
            ))

        return issues

    def validate_replay(self, replay: Dict[str, Any]) -> Dict[str, Any]:
        replay = _safe_dict(replay)
        frames = _safe_list(replay.get("frames"))

        issues: List[ReplayValidationIssue] = []

        if replay.get("read_only") is not True:
            issues.append(ReplayValidationIssue(
                frame_id="replay",
                severity="critical",
                code="replay_read_only_violation",
                message="Replay package is not marked read_only=True.",
            ))

        if replay.get("execution_allowed") is not False:
            issues.append(ReplayValidationIssue(
                frame_id="replay",
                severity="critical",
                code="replay_execution_violation",
                message="Replay package allows execution. Oracle must remain read-only.",
            ))

        if replay.get("execution_owner") != "Q Series":
            issues.append(ReplayValidationIssue(
                frame_id="replay",
                severity="critical",
                code="replay_execution_owner_violation",
                message="Replay package execution_owner must be Q Series.",
            ))

        declared_count = int(_num(replay.get("frame_count"), len(frames)))
        if declared_count != len(frames):
            issues.append(ReplayValidationIssue(
                frame_id="replay",
                severity="warning",
                code="frame_count_mismatch",
                message=f"Replay frame_count is {declared_count}, but {len(frames)} frames were found.",
            ))

        seen_ids = set()
        for idx, frame in enumerate(frames, start=1):
            frame = _safe_dict(frame)
            frame_id = str(frame.get("replay_frame_id") or "")
            if frame_id and frame_id in seen_ids:
                issues.append(ReplayValidationIssue(
                    frame_id=frame_id,
                    severity="critical",
                    code="duplicate_frame_id",
                    message="Duplicate replay_frame_id detected.",
                ))
            if frame_id:
                seen_ids.add(frame_id)

            issues.extend(self._validate_frame(frame, idx))

        critical_count = sum(1 for issue in issues if issue.severity == "critical")
        warning_count = sum(1 for issue in issues if issue.severity == "warning")

        validation_status = "validated"
        if critical_count:
            validation_status = "failed"
        elif warning_count:
            validation_status = "validated_with_warnings"

        validation_id = _hash({
            "replay_id": replay.get("replay_id"),
            "frame_count": len(frames),
            "issues": [issue.__dict__ for issue in issues],
        })

        return {
            "module": self.name,
            "version": self.version,
            "validation_schema_version": self.validation_schema_version,
            "validation_id": validation_id,
            "validated_at": _utc_now(),
            "source_replay_id": replay.get("replay_id"),
            "validation_status": validation_status,
            "read_only": self.read_only,
            "execution_allowed": self.execution_allowed,
            "execution_owner": self.execution_owner,
            "frame_count": len(frames),
            "issue_count": len(issues),
            "critical_count": critical_count,
            "warning_count": warning_count,
            "summary": {
                "headline": (
                    "Replay validation passed."
                    if validation_status == "validated"
                    else f"Replay validation status: {validation_status}."
                ),
                "validation_id": validation_id,
                "source_replay_id": replay.get("replay_id"),
                "frame_count": len(frames),
                "issue_count": len(issues),
                "critical_count": critical_count,
                "warning_count": warning_count,
                "read_only": True,
                "execution_allowed": False,
                "execution_owner": self.execution_owner,
            },
            "issues": [issue.__dict__ for issue in issues],
        }


oracle_replay_validation_engine = OracleReplayValidationEngine()
