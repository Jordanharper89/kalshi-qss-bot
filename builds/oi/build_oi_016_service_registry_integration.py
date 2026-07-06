"""
build_oi_016_service_registry_integration.py
OI-016 Oracle Service Registry Integration Installer
"""

from pathlib import Path
from datetime import datetime

ROOT = Path.cwd()
OI = ROOT / "qseries_v2" / "oi"


def backup(path):
    if path.exists():
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        bak = path.with_suffix(path.suffix + f".bak_{stamp}")
        bak.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        backup(path)
    path.write_text(text, encoding="utf-8")
    print(f"[OK] Wrote {path.relative_to(ROOT)}")


registry_code = '''"""
OI-016 Oracle Service Registry Integration

Registers Oracle Intelligence with CORE-001 Service Registry.
"""

from qseries_v2.core.service_registry import service_registry
from .oracle_intelligence_service import oracle_intelligence_service


def register_oracle_intelligence(replace=True):
    return service_registry.register(
        service_id=oracle_intelligence_service.service_id,
        name=oracle_intelligence_service.name,
        category=oracle_intelligence_service.category,
        instance=oracle_intelligence_service,
        version=oracle_intelligence_service.version,
        description="Oracle Intelligence researches, scores, explains, and learns. Oracle never executes trades.",
        healthcheck=oracle_intelligence_service.health,
        tags=["oracle", "intelligence", "research", "learning"],
        replace=replace,
    )


def get_oracle_intelligence():
    return service_registry.get(oracle_intelligence_service.service_id)
'''

test_code = '''from qseries_v2.oi.service_registry_integration import (
    register_oracle_intelligence,
    get_oracle_intelligence,
)
from qseries_v2.core.service_registry import service_registry

record = register_oracle_intelligence(replace=True)
service = get_oracle_intelligence()
health = service_registry.health("oracle.intelligence")

assert record.meta.service_id == "oracle.intelligence"
assert service is not None
assert health["health"]["ok"] is True
assert health["health"]["oracle_executes"] is False

print("[PASS] OI-016 Service Registry Integration")
print(service_registry.diagnostics())
'''

init_code = '''from .evidence_engine import evidence_engine, EvidenceEngine, Evidence
from .confidence_engine import confidence_engine, ConfidenceEngine
from .probability_engine import probability_engine, ProbabilityEngine
from .recommendation_engine import recommendation_engine, RecommendationEngine
from .explanation_engine import explanation_engine, ExplanationEngine
from .decision_pipeline import oracle_decision_pipeline, OracleDecisionPipeline
from .learning_ledger import learning_ledger, LearningLedger, LearningRecord
from .performance_review import performance_review_engine, PerformanceReviewEngine
from .learning_feedback import learning_feedback_engine, LearningFeedbackEngine
from .learning_loop import oracle_learning_loop, OracleLearningLoop
from .calibration_engine import calibration_engine, CalibrationEngine
from .calibrated_pipeline import calibrated_decision_pipeline, CalibratedDecisionPipeline
from .research_report import research_report_engine, ResearchReportEngine
from .research_packet import research_packet_engine, ResearchPacketEngine
from .oracle_intelligence_service import oracle_intelligence_service, OracleIntelligenceService
from .service_registry_integration import register_oracle_intelligence, get_oracle_intelligence
'''

print("=" * 40)
print(" OI-016 INSTALLER")
print(" Service Registry Integration")
print("=" * 40)

write(OI / "service_registry_integration.py", registry_code)
write(OI / "__init__.py", init_code)
write(ROOT / "test_oi_016_service_registry_integration.py", test_code)

print("\n[DONE] OI-016 installed")
print("\nRun:")
print("python test_oi_016_service_registry_integration.py")