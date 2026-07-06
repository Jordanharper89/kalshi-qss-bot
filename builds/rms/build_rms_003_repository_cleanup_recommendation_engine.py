from pathlib import Path

ROOT = Path.cwd()
PKG = ROOT / "qseries_v2" / "repository_management"
TEST_DIR = ROOT / "tests" / "rms"

MODULE = PKG / "repository_cleanup_recommendation_engine.py"
INIT = PKG / "__init__.py"
TEST = TEST_DIR / "test_rms_003_repository_cleanup_recommendation_engine.py"

MODULE_CODE = r'''
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Dict, Iterable, List, Mapping


ENGINE_ID = "RMS-003"
ENGINE_NAME = "Repository Cleanup Recommendation Engine"
ENGINE_VERSION = "1.0.0"


@dataclass(frozen=True)
class RepositoryCleanupRecommendation:
    path: str
    name: str
    classification: str
    action: str
    recommendation: str
    risk_level: str
    safe_to_automate: bool
    reason: str


@dataclass(frozen=True)
class RepositoryCleanupRecommendationResult:
    engine_id: str
    engine_name: str
    engine_version: str
    input_count: int
    recommendation_count: int
    action_counts: Dict[str, int]
    risk_counts: Dict[str, int]
    recommendations: List[RepositoryCleanupRecommendation]
    telemetry: Dict[str, Any]
    explanation: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "engine_id": self.engine_id,
            "engine_name": self.engine_name,
            "engine_version": self.engine_version,
            "input_count": self.input_count,
            "recommendation_count": self.recommendation_count,
            "action_counts": dict(self.action_counts),
            "risk_counts": dict(self.risk_counts),
            "recommendations": [asdict(item) for item in self.recommendations],
            "telemetry": dict(self.telemetry),
            "explanation": self.explanation,
        }


class RepositoryCleanupRecommendationEngine:
    def recommend(self, classification_result: Any) -> RepositoryCleanupRecommendationResult:
        records = self._extract_records(classification_result)
        recommendations: List[RepositoryCleanupRecommendation] = []

        for raw in records:
            record = self._to_mapping(raw)
            if not record:
                continue
            recommendations.append(self._recommend_one(record))

        action_counts: Dict[str, int] = {}
        risk_counts: Dict[str, int] = {}

        for item in recommendations:
            action_counts[item.recommendation] = action_counts.get(item.recommendation, 0) + 1
            risk_counts[item.risk_level] = risk_counts.get(item.risk_level, 0) + 1

        return RepositoryCleanupRecommendationResult(
            engine_id=ENGINE_ID,
            engine_name=ENGINE_NAME,
            engine_version=ENGINE_VERSION,
            input_count=len(records),
            recommendation_count=len(recommendations),
            action_counts=dict(sorted(action_counts.items())),
            risk_counts=dict(sorted(risk_counts.items())),
            recommendations=recommendations,
            telemetry={
                "engine_id": ENGINE_ID,
                "engine_name": ENGINE_NAME,
                "engine_version": ENGINE_VERSION,
                "repository_role": "architecture_support",
                "does_not_modify_files": True,
                "does_not_delete_files": True,
                "does_not_move_files": True,
                "recommendation_only": True,
                "input_contract": "RepositoryClassificationResult compatible",
                "output_contract": "RepositoryCleanupRecommendationResult",
            },
            explanation=(
                f"Generated {len(recommendations)} cleanup recommendation(s) from "
                f"{len(records)} classified repository record(s). This engine is advisory only."
            ),
        )

    def _recommend_one(self, record: Mapping[str, Any]) -> RepositoryCleanupRecommendation:
        path = str(record.get("path", ""))
        name = str(record.get("name", path))
        classification = str(record.get("classification", "UNKNOWN"))
        action = str(record.get("action", "review"))

        if classification == "SECRET":
            return self._rec(record, "ignore_never_commit", "critical", True, "Secret file must remain ignored and must never be committed.")

        if classification == "RUNTIME":
            return self._rec(record, "ignore_runtime", "low", True, "Runtime/generated file should stay ignored by Git.")

        if classification == "ACCIDENTAL_JUNK":
            return self._rec(record, "delete_after_confirming_zero_byte", "low", True, "Numeric zero-byte artifact appears accidental and can be deleted after size verification.")

        if classification == "ARCHIVE":
            return self._rec(record, "keep_ignored_or_archive", "medium", False, "Backup or historical artifact should not be active source; archive or ignore it.")

        if classification in {"BUILD_INSTALLER", "TEST", "SCRIPT", "DOCUMENTATION", "CONFIG"}:
            return self._rec(record, "keep", "low", True, "Repository support artifact is already in the correct class.")

        if classification in {"ACTIVE_PLATFORM_SOURCE", "ACTIVE_PROVIDER_SOURCE", "ACTIVE_SUPPORT_SOURCE"}:
            return self._rec(record, "keep_active_source", "low", True, "Active source folder should be kept and committed.")

        if classification == "LEGACY_ORACLE_MODULE":
            return self._rec(record, "review_legacy_oracle_before_move", "high", False, "Legacy Oracle module may still support active workflows; inspect imports before moving.")

        if classification == "LEGACY_ORACLE_FOLDER":
            return self._rec(record, "review_legacy_oracle_folder", "high", False, "Legacy Oracle folder requires dependency review before migration.")

        if classification == "ROOT_SOURCE_MODULE":
            return self._rec(record, "review_root_source_before_migration", "medium", False, "Root-level source should be classified by subsystem before moving.")

        return self._rec(record, "manual_review", "medium", False, "Repository item requires manual review.")

    def _rec(
        self,
        record: Mapping[str, Any],
        recommendation: str,
        risk_level: str,
        safe_to_automate: bool,
        reason: str,
    ) -> RepositoryCleanupRecommendation:
        return RepositoryCleanupRecommendation(
            path=str(record.get("path", "")),
            name=str(record.get("name", record.get("path", ""))),
            classification=str(record.get("classification", "UNKNOWN")),
            action=str(record.get("action", "review")),
            recommendation=recommendation,
            risk_level=risk_level,
            safe_to_automate=bool(safe_to_automate),
            reason=reason,
        )

    def _extract_records(self, result: Any) -> List[Any]:
        if result is None:
            return []
        if isinstance(result, Mapping):
            raw = result.get("records", [])
            return list(raw) if isinstance(raw, Iterable) and not isinstance(raw, (str, bytes)) else []
        if hasattr(result, "records"):
            raw = getattr(result, "records")
            return list(raw) if isinstance(raw, Iterable) and not isinstance(raw, (str, bytes)) else []
        if isinstance(result, Iterable) and not isinstance(result, (str, bytes)):
            return list(result)
        return []

    def _to_mapping(self, item: Any) -> Dict[str, Any]:
        if item is None:
            return {}
        if isinstance(item, Mapping):
            return dict(item)
        if hasattr(item, "to_dict") and callable(item.to_dict):
            mapped = item.to_dict()
            return dict(mapped) if isinstance(mapped, Mapping) else {}
        if hasattr(item, "__dict__"):
            return dict(vars(item))
        return {}


def recommend_repository_cleanup(classification_result: Any) -> RepositoryCleanupRecommendationResult:
    return RepositoryCleanupRecommendationEngine().recommend(classification_result)


__all__ = [
    "ENGINE_ID",
    "ENGINE_NAME",
    "ENGINE_VERSION",
    "RepositoryCleanupRecommendation",
    "RepositoryCleanupRecommendationResult",
    "RepositoryCleanupRecommendationEngine",
    "recommend_repository_cleanup",
]
'''

TEST_CODE = r'''
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from qseries_v2.repository_management.repository_inventory_engine import scan_repository
from qseries_v2.repository_management.repository_classification_engine import classify_repository_inventory
from qseries_v2.repository_management.repository_cleanup_recommendation_engine import recommend_repository_cleanup


def test_cleanup_recommendations_from_live_repo():
    inventory = scan_repository(ROOT)
    classification = classify_repository_inventory(inventory)
    result = recommend_repository_cleanup(classification)

    assert result.engine_id == "RMS-003"
    assert result.input_count > 0
    assert result.recommendation_count > 0
    assert result.telemetry["does_not_delete_files"] is True
    assert result.telemetry["does_not_move_files"] is True
    assert result.action_counts


def test_secret_gets_never_commit_recommendation():
    result = recommend_repository_cleanup(
        {"records": [{"path": ".env", "name": ".env", "classification": "SECRET", "action": "ignore"}]}
    )

    assert result.recommendations[0].recommendation == "ignore_never_commit"
    assert result.recommendations[0].risk_level == "critical"


def test_junk_gets_delete_candidate_recommendation():
    result = recommend_repository_cleanup(
        {"records": [{"path": "10", "name": "10", "classification": "ACCIDENTAL_JUNK", "action": "delete_candidate"}]}
    )

    assert result.recommendations[0].recommendation == "delete_after_confirming_zero_byte"
    assert result.recommendations[0].safe_to_automate is True


if __name__ == "__main__":
    test_cleanup_recommendations_from_live_repo()
    test_secret_gets_never_commit_recommendation()
    test_junk_gets_delete_candidate_recommendation()

    inventory = scan_repository(ROOT)
    classification = classify_repository_inventory(inventory)
    result = recommend_repository_cleanup(classification)

    print("[PASS] RMS-003 Repository Cleanup Recommendation Engine")
    print(result.to_dict())
'''


def update_init() -> None:
    existing = INIT.read_text(encoding="utf-8") if INIT.exists() else ""
    lines = [
        "from .repository_inventory_engine import RepositoryInventoryEngine, scan_repository\n",
        "from .repository_classification_engine import RepositoryClassificationEngine, classify_repository_inventory\n",
        "from .repository_cleanup_recommendation_engine import RepositoryCleanupRecommendationEngine, recommend_repository_cleanup\n",
    ]
    for line in lines:
        if line not in existing:
            existing += line
    INIT.write_text(existing, encoding="utf-8")


def main():
    PKG.mkdir(parents=True, exist_ok=True)
    TEST_DIR.mkdir(parents=True, exist_ok=True)

    MODULE.write_text(MODULE_CODE.strip() + "\n", encoding="utf-8")
    TEST.write_text(TEST_CODE.strip() + "\n", encoding="utf-8")
    update_init()

    print("========================================")
    print(" RMS-003 INSTALLER")
    print(" Repository Cleanup Recommendation Engine")
    print("========================================")
    print(f"[OK] Wrote {MODULE}")
    print(f"[OK] Wrote {TEST}")
    print(f"[OK] Updated {INIT}")
    print()
    print("[DONE] RMS-003 installed")
    print()
    print("Run:")
    print("py tests\\rms\\test_rms_003_repository_cleanup_recommendation_engine.py")


if __name__ == "__main__":
    main()