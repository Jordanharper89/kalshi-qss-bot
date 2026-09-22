"""SLOP entry points into the existing OOS. No execution authority."""
from qseries_v2.oracle_strategy_intelligence.oracle_opportunity_intelligence.ooi_006_slop_universal_opportunity_materializer import materialize_slop
from qseries_v2.oracle_intelligence.opportunity_operating_system.opportunity_operating_system import OpportunityOperatingSystem

EXECUTION_AUTHORITY = False
READ_ONLY = True
SOURCE = 'SLOP_BUY_PRESSURE'

def _canonical(source):
    opportunity = materialize_slop(source)
    if opportunity.read_only is not True or opportunity.metadata.get('execution_authority') is not False:
        raise ValueError('Oracle read-only boundary violated')
    opportunity.fingerprint()
    return opportunity

def intake_slop(source, oos):
    """Register research in the caller-owned existing OOS; not trade approval."""
    if not isinstance(oos, OpportunityOperatingSystem):
        raise TypeError('An existing OpportunityOperatingSystem instance is required')
    opportunity = _canonical(source)
    result = oos.intake(opportunity, source=SOURCE, metadata={'execution_authority': False, 'read_only': True})
    return opportunity, result

from qseries_v2.oracle_intelligence.opportunity_operating_system.opportunity_validation_engine import OpportunityValidationEngine, ValidationRuleConfig

def _validate(opportunity):
    # Preserve the existing production validation defaults, including UNKNOWN handling.
    return OpportunityValidationEngine(config=ValidationRuleConfig()).validate(opportunity)

def validate_slop(source):
    opportunity = _canonical(source)
    report = _validate(opportunity)
    return opportunity, report

from qseries_v2.oracle_intelligence.opportunity_operating_system.opportunity_ranking_engine import OpportunityRankingEngine

def _partition(sources):
    accepted, reports = [], []
    for source in sources:
        opportunity, report = validate_slop(source)
        reports.append(report)
        if report.is_accepted():
            accepted.append(opportunity)
    return accepted, reports

def rank_validated_slop(sources):
    accepted, reports = _partition(sources)
    result = OpportunityRankingEngine().rank(accepted)
    return result, reports

from qseries_v2.oracle_intelligence.opportunity_operating_system.opportunity_pipeline import OpportunityPipeline

def process_validated_slop(sources, oos):
    """Only accepted research reaches the caller-owned registry and ranking pipeline."""
    if not isinstance(oos, OpportunityOperatingSystem):
        raise TypeError('An existing OpportunityOperatingSystem instance is required')
    accepted, reports = _partition(sources)
    pipeline = OpportunityPipeline(oos=oos, ranking_engine=OpportunityRankingEngine())
    result = pipeline.process(accepted, source=SOURCE)
    return result, reports

def process_evidence_backed_slop(sources, evidence_snapshot, oos, policy=None, evaluated_at=None):
    """Research-only evidence handoff into the existing registry/validator/ranker."""
    if not isinstance(oos, OpportunityOperatingSystem):
        raise TypeError('Existing OpportunityOperatingSystem instance required')
    accepted, reports, held = [], [], []
    for source in sources:
        opportunity = materialize_slop(source, evidence_snapshot=evidence_snapshot,
                                       policy=policy, evaluated_at=evaluated_at)
        if opportunity.read_only is not True or opportunity.metadata['execution_authority'] is not False:
            raise ValueError('Oracle authority boundary violated')
        report = _validate(opportunity)
        reports.append(report)
        if opportunity.metadata.get('evidence_admission_eligible') is True and report.is_accepted():
            accepted.append(opportunity)
        else:
            held.append({'opportunity_id': opportunity.opportunity_id,
                         'reasons': opportunity.metadata.get('evidence_hold_reasons', []),
                         'validation_accepted': report.is_accepted()})
    pipeline = OpportunityPipeline(oos=oos, ranking_engine=OpportunityRankingEngine())
    result = pipeline.process(accepted, source=SOURCE)
    return {'pipeline': result, 'validation_reports': reports, 'held': held,
            'accepted_count': len(accepted), 'read_only': True, 'execution_authority': False}
