"""
OIA-015
Oracle Forward Shadow Ranking Eligibility Gate

Combines immutable calibration, reliability, and statistical-confidence reports
into deterministic research-only ranking eligibility decisions. No signals,
alerts, recommendations, Q Series handoffs, or execution.
"""
from __future__ import annotations

import argparse, hashlib, json, os, tempfile
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping

from .oracle_forward_shadow_calibration_analyzer import DEFAULT_CALIBRATION_DIRECTORY, stable_hash as calibration_stable_hash
from .oracle_forward_shadow_reliability_decomposition_engine import DEFAULT_RELIABILITY_DIRECTORY, stable_hash as reliability_stable_hash
from .oracle_forward_shadow_statistical_confidence_engine import DEFAULT_CONFIDENCE_DIRECTORY, stable_hash as confidence_stable_hash

SCHEMA_VERSION = "OIA-015"
ENGINE_ID = "OIA-015"
ELIGIBLE = "eligible"
PROVISIONAL = "provisional"
INELIGIBLE = "ineligible"
INSUFFICIENT_EVIDENCE = "insufficient_evidence"
READ_ONLY_CORPUS = True
EXECUTION_ALLOWED = False
ALERTS_ALLOWED = False
QSERIES_HANDOFF_ALLOWED = False
SIGNALS_ALLOWED = False
TRADING_RECOMMENDATIONS_ALLOWED = False
SOURCE_MUTATION_ALLOWED = False
ELIGIBILITY_ARTIFACT_PERSISTENCE_ALLOWED = True
DEFAULT_ELIGIBILITY_DIRECTORY = Path("runtime") / "oracle_intelligence" / "forward_shadow_ranking_eligibility"

class ForwardShadowRankingEligibilityError(RuntimeError): pass
class ForwardShadowRankingEligibilityInvariantError(ForwardShadowRankingEligibilityError): pass

def _aware_utc(value: datetime, name: str) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise ForwardShadowRankingEligibilityInvariantError(f"{name} must be timezone-aware.")
    return value.astimezone(timezone.utc)

def _canonical(value: Any) -> Any:
    if is_dataclass(value): return _canonical(asdict(value))
    if isinstance(value, Mapping): return {str(k): _canonical(v) for k,v in value.items()}
    if isinstance(value, (list,tuple)): return [_canonical(v) for v in value]
    if isinstance(value, datetime): return _aware_utc(value,"datetime").isoformat()
    if isinstance(value, Decimal): return format(value,"f")
    return value

def stable_hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(_canonical(value),sort_keys=True,separators=(",",":"),ensure_ascii=False,allow_nan=False).encode()).hexdigest()

def _freeze(value: Mapping[str,Any]) -> Mapping[str,Any]: return MappingProxyType(dict(value))

def _decimal(value: Any, name: str) -> Decimal:
    try: result=Decimal(str(value))
    except (InvalidOperation,ValueError,TypeError) as exc: raise ForwardShadowRankingEligibilityInvariantError(f"{name} must be a finite decimal.") from exc
    if not result.is_finite(): raise ForwardShadowRankingEligibilityInvariantError(f"{name} must be a finite decimal.")
    return result

def _atomic(path: Path, payload: Mapping[str,Any]) -> None:
    path.parent.mkdir(parents=True,exist_ok=True)
    data=json.dumps(_canonical(payload),sort_keys=True,indent=2,ensure_ascii=False)+"\n"
    handle=tempfile.NamedTemporaryFile("w",encoding="utf-8",newline="\n",delete=False,dir=str(path.parent),prefix=f".{path.name}.",suffix=".tmp")
    temp=Path(handle.name)
    try:
        with handle:
            handle.write(data); handle.flush(); os.fsync(handle.fileno())
        os.replace(temp,path)
    finally:
        if temp.exists(): temp.unlink()

@dataclass(frozen=True)
class OracleForwardShadowRankingEligibilityDecision:
    dimension: str
    key: str
    status: str
    decisive_count: int
    empirical_win_rate: str
    confidence_lower_bound: str
    confidence_upper_bound: str
    calibration_error: str
    brier_score: str
    reliability: str
    resolution: str
    evidence_sufficiency: str
    sample_sufficiency: str
    reason_codes: tuple[str,...]
    calibration_bucket_hash: str
    reliability_component_hash: str
    confidence_component_hash: str
    decision_hash: str
    def to_dict(self) -> Mapping[str,Any]: return _freeze(_canonical(asdict(self)))

@dataclass(frozen=True)
class OracleForwardShadowRankingEligibilityReport:
    schema_version: str
    engine_id: str
    generated_at: datetime
    calibration_directory: str
    reliability_directory: str
    confidence_directory: str
    eligibility_directory: str
    matched_component_count: int
    eligible_count: int
    provisional_count: int
    ineligible_count: int
    insufficient_evidence_count: int
    decisions: tuple[OracleForwardShadowRankingEligibilityDecision,...]
    source_calibration_report_hash: str
    source_reliability_report_hash: str
    source_confidence_report_hash: str
    read_only_corpus: bool
    execution_allowed: bool
    alerts_allowed: bool
    qseries_handoff_allowed: bool
    signals_allowed: bool
    trading_recommendations_allowed: bool
    source_mutation_allowed: bool
    eligibility_artifact_persistence_allowed: bool
    report_hash: str
    def to_dict(self) -> Mapping[str,Any]: return _freeze(_canonical(asdict(self)))

class OracleForwardShadowRankingEligibilityGate:
    read_only_corpus=True; execution_allowed=False; alerts_allowed=False; qseries_handoff_allowed=False; signals_allowed=False
    trading_recommendations_allowed=False; source_mutation_allowed=False; eligibility_artifact_persistence_allowed=True
    def __init__(self, *, calibration_directory: Path|str=DEFAULT_CALIBRATION_DIRECTORY, reliability_directory: Path|str=DEFAULT_RELIABILITY_DIRECTORY, confidence_directory: Path|str=DEFAULT_CONFIDENCE_DIRECTORY, eligibility_directory: Path|str=DEFAULT_ELIGIBILITY_DIRECTORY, max_calibration_error: Decimal|str="0.10", max_brier_score: Decimal|str="0.25", max_reliability: Decimal|str="0.05") -> None:
        self._calibration_directory=Path(calibration_directory); self._reliability_directory=Path(reliability_directory); self._confidence_directory=Path(confidence_directory); self._eligibility_directory=Path(eligibility_directory)
        self._max_calibration_error=_decimal(max_calibration_error,"max_calibration_error"); self._max_brier_score=_decimal(max_brier_score,"max_brier_score"); self._max_reliability=_decimal(max_reliability,"max_reliability")
        if min(self._max_calibration_error,self._max_brier_score,self._max_reliability) < 0: raise ForwardShadowRankingEligibilityInvariantError("Eligibility thresholds must be non-negative.")
    @staticmethod
    def _load_report(directory: Path, expected: str, hasher, label: str) -> dict[str,Any]:
        path=directory/"current.json"
        if not path.exists(): raise ForwardShadowRankingEligibilityInvariantError(f"{label} current report missing: {path}")
        payload=json.loads(path.read_text(encoding="utf-8")); digest=payload.pop("report_hash",None)
        if payload.get("schema_version")!=expected or payload.get("engine_id")!=expected: raise ForwardShadowRankingEligibilityInvariantError(f"Unsupported {label} report identity: {path}")
        if digest!=hasher(payload): raise ForwardShadowRankingEligibilityInvariantError(f"{label} report hash verification failed: {path}")
        payload["report_hash"]=digest; return payload
    def _decision(self, calibration: Mapping[str,Any], reliability: Mapping[str,Any], confidence: Mapping[str,Any]) -> OracleForwardShadowRankingEligibilityDecision:
        if calibration["dimension"]!=reliability["dimension"] or calibration["dimension"]!=confidence["dimension"] or calibration["key"]!=reliability["key"] or calibration["key"]!=confidence["key"]: raise ForwardShadowRankingEligibilityInvariantError("Joined component identity mismatch.")
        calerr=_decimal(calibration["calibration_error"],"calibration_error"); brier=_decimal(calibration["brier_score"],"brier_score"); rel=_decimal(reliability["reliability"],"reliability"); lower=_decimal(confidence["lower_bound"],"lower_bound")
        evidence=str(confidence["evidence_sufficiency"]); sample=str(reliability["sample_sufficiency"]); reasons=[]
        adverse=bool(confidence["statistically_below_chance"]) or calerr>self._max_calibration_error or brier>self._max_brier_score or rel>self._max_reliability
        mature=evidence in {"established","strong"} and sample=="established"
        if adverse:
            status=INELIGIBLE
            if confidence["statistically_below_chance"]: reasons.append("statistically_below_chance")
            if calerr>self._max_calibration_error: reasons.append("calibration_error_exceeds_policy")
            if brier>self._max_brier_score: reasons.append("brier_score_exceeds_policy")
            if rel>self._max_reliability: reasons.append("reliability_error_exceeds_policy")
        elif mature and lower>Decimal("0.5"):
            status=ELIGIBLE; reasons.extend(("evidence_sufficient","confidence_above_chance","calibration_within_policy","reliability_within_policy"))
        elif evidence in {"provisional","established","strong"} or sample=="provisional":
            status=PROVISIONAL; reasons.append("evidence_provisional")
            if lower<=Decimal("0.5"): reasons.append("confidence_not_yet_above_chance")
        else:
            status=INSUFFICIENT_EVIDENCE; reasons.append("minimum_evidence_not_met")
        body={"dimension":str(calibration["dimension"]),"key":str(calibration["key"]),"status":status,"decisive_count":int(confidence["decisive_count"]),"empirical_win_rate":str(calibration["empirical_win_rate"]),"confidence_lower_bound":str(confidence["lower_bound"]),"confidence_upper_bound":str(confidence["upper_bound"]),"calibration_error":str(calibration["calibration_error"]),"brier_score":str(calibration["brier_score"]),"reliability":str(reliability["reliability"]),"resolution":str(reliability["resolution"]),"evidence_sufficiency":evidence,"sample_sufficiency":sample,"reason_codes":tuple(reasons),"calibration_bucket_hash":str(calibration["bucket_hash"]),"reliability_component_hash":str(reliability["component_hash"]),"confidence_component_hash":str(confidence["component_hash"])}
        return OracleForwardShadowRankingEligibilityDecision(**body,decision_hash=stable_hash(body))
    def evaluate(self, *, generated_at: datetime|None=None, persist: bool=True) -> OracleForwardShadowRankingEligibilityReport:
        generated_at=_aware_utc(generated_at or datetime.now(timezone.utc),"generated_at")
        cal=self._load_report(self._calibration_directory,"OIA-012",calibration_stable_hash,"OIA-012 calibration")
        rel=self._load_report(self._reliability_directory,"OIA-013",reliability_stable_hash,"OIA-013 reliability")
        conf=self._load_report(self._confidence_directory,"OIA-014",confidence_stable_hash,"OIA-014 confidence")
        cmap={(x["dimension"],x["key"]):x for x in cal["buckets"]}; rmap={(x["dimension"],x["key"]):x for x in rel["components"]}; fmap={(x["dimension"],x["key"]):x for x in conf["components"]}
        keys=sorted(set(cmap)&set(rmap)&set(fmap)); decisions=tuple(self._decision(cmap[k],rmap[k],fmap[k]) for k in keys)
        body={"schema_version":SCHEMA_VERSION,"engine_id":ENGINE_ID,"generated_at":generated_at,"calibration_directory":str(self._calibration_directory),"reliability_directory":str(self._reliability_directory),"confidence_directory":str(self._confidence_directory),"eligibility_directory":str(self._eligibility_directory),"matched_component_count":len(decisions),"eligible_count":sum(d.status==ELIGIBLE for d in decisions),"provisional_count":sum(d.status==PROVISIONAL for d in decisions),"ineligible_count":sum(d.status==INELIGIBLE for d in decisions),"insufficient_evidence_count":sum(d.status==INSUFFICIENT_EVIDENCE for d in decisions),"decisions":decisions,"source_calibration_report_hash":cal["report_hash"],"source_reliability_report_hash":rel["report_hash"],"source_confidence_report_hash":conf["report_hash"],"read_only_corpus":True,"execution_allowed":False,"alerts_allowed":False,"qseries_handoff_allowed":False,"signals_allowed":False,"trading_recommendations_allowed":False,"source_mutation_allowed":False,"eligibility_artifact_persistence_allowed":True}
        report=OracleForwardShadowRankingEligibilityReport(**body,report_hash=stable_hash(body))
        if persist:
            payload=dict(report.to_dict()); _atomic(self._eligibility_directory/"current.json",payload); _atomic(self._eligibility_directory/"reports"/f"eligibility-{report.report_hash}.json",payload)
        return report

def main(argv=None) -> int:
    parser=argparse.ArgumentParser(description="OIA-015 forward-shadow ranking eligibility gate")
    parser.add_argument("--calibration-directory",default=str(DEFAULT_CALIBRATION_DIRECTORY)); parser.add_argument("--reliability-directory",default=str(DEFAULT_RELIABILITY_DIRECTORY)); parser.add_argument("--confidence-directory",default=str(DEFAULT_CONFIDENCE_DIRECTORY)); parser.add_argument("--eligibility-directory",default=str(DEFAULT_ELIGIBILITY_DIRECTORY)); parser.add_argument("--no-persist",action="store_true")
    args=parser.parse_args(argv); report=OracleForwardShadowRankingEligibilityGate(calibration_directory=args.calibration_directory,reliability_directory=args.reliability_directory,confidence_directory=args.confidence_directory,eligibility_directory=args.eligibility_directory).evaluate(persist=not args.no_persist)
    print("========================================"); print(" OIA-015 RANKING ELIGIBILITY"); print(" RESEARCH-ONLY MULTI-EVIDENCE GATE"); print("========================================"); print(f"[RESULT] Matched components: {report.matched_component_count}"); print(f"[RESULT] Eligible: {report.eligible_count}"); print(f"[RESULT] Provisional: {report.provisional_count}"); print(f"[RESULT] Ineligible: {report.ineligible_count}"); print(f"[RESULT] Insufficient evidence: {report.insufficient_evidence_count}"); print(f"[RESULT] Report hash: {report.report_hash}"); return 0
if __name__=="__main__": raise SystemExit(main())
