"""
OIA-013
Oracle Forward Shadow Reliability Decomposition Engine

Decomposes immutable forward-shadow probability forecasts and realized decisive
outcomes into Brier reliability, resolution, uncertainty, and sample-sufficiency
components. Research analytics only; no signals, alerts, recommendations, or execution.
"""
from __future__ import annotations

import argparse, hashlib, json, os, tempfile
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation, ROUND_HALF_EVEN
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping, Optional

from .oracle_forward_shadow_evaluation_ledger import DEFAULT_LEDGER_DIRECTORY, OracleForwardShadowEvaluationLedger
from .oracle_forward_shadow_outcome_evaluator import DEFAULT_OUTCOME_DIRECTORY, LOSS, WIN, stable_hash as outcome_stable_hash

SCHEMA_VERSION = "OIA-013"
ENGINE_ID = "OIA-013"
READ_ONLY_CORPUS = True
EXECUTION_ALLOWED = False
ALERTS_ALLOWED = False
QSERIES_HANDOFF_ALLOWED = False
SIGNALS_ALLOWED = False
TRADING_RECOMMENDATIONS_ALLOWED = False
SOURCE_MUTATION_ALLOWED = False
RELIABILITY_ARTIFACT_PERSISTENCE_ALLOWED = True
DEFAULT_RELIABILITY_DIRECTORY = Path("runtime") / "oracle_intelligence" / "forward_shadow_reliability"
DEFAULT_SCORE_BANDS = ((0, 59), (60, 69), (70, 79), (80, 89), (90, 100))
_QUANT = Decimal("0.00000001")

class ForwardShadowReliabilityError(RuntimeError): pass
class ForwardShadowReliabilityInvariantError(ForwardShadowReliabilityError): pass

def _aware_utc(value: datetime, name: str) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise ForwardShadowReliabilityInvariantError(f"{name} must be timezone-aware.")
    return value.astimezone(timezone.utc)

def _canonical(value: Any) -> Any:
    if is_dataclass(value): return _canonical(asdict(value))
    if isinstance(value, Mapping): return {str(k): _canonical(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)): return [_canonical(v) for v in value]
    if isinstance(value, datetime): return _aware_utc(value, "datetime").isoformat()
    if isinstance(value, Decimal): return format(value, "f")
    return value

def stable_hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(_canonical(value), sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()).hexdigest()

def _freeze(value: Mapping[str, Any]) -> Mapping[str, Any]: return MappingProxyType(dict(value))

def _decimal(value: Any, name: str) -> Decimal:
    try: result = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError) as exc: raise ForwardShadowReliabilityInvariantError(f"{name} must be a finite decimal.") from exc
    if not result.is_finite(): raise ForwardShadowReliabilityInvariantError(f"{name} must be a finite decimal.")
    return result

def _fmt(value: Decimal) -> str: return format(value.quantize(_QUANT, rounding=ROUND_HALF_EVEN), "f")

def _atomic(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(_canonical(payload), sort_keys=True, indent=2, ensure_ascii=False) + "\n"
    handle = tempfile.NamedTemporaryFile("w", encoding="utf-8", newline="\n", delete=False, dir=str(path.parent), prefix=f".{path.name}.", suffix=".tmp")
    temp = Path(handle.name)
    try:
        with handle:
            handle.write(data); handle.flush(); os.fsync(handle.fileno())
        os.replace(temp, path)
    finally:
        if temp.exists(): temp.unlink()

@dataclass(frozen=True)
class OracleForwardShadowReliabilityComponent:
    dimension: str
    key: str
    decisive_count: int
    win_count: int
    loss_count: int
    base_rate: str
    brier_score: str
    reliability: str
    resolution: str
    uncertainty: str
    decomposition_brier_score: str
    decomposition_error: str
    sample_sufficiency: str
    probability_band_count: int
    component_hash: str
    def to_dict(self) -> Mapping[str, Any]: return _freeze(_canonical(asdict(self)))

@dataclass(frozen=True)
class OracleForwardShadowReliabilityReport:
    schema_version: str
    engine_id: str
    generated_at: datetime
    ledger_directory: str
    outcome_directory: str
    reliability_directory: str
    ledger_entry_count: int
    verified_outcome_count: int
    joined_decisive_count: int
    unmatched_outcome_count: int
    duplicate_outcome_count: int
    component_count: int
    components: tuple[OracleForwardShadowReliabilityComponent, ...]
    source_entry_hashes: tuple[str, ...]
    source_outcome_hashes: tuple[str, ...]
    read_only_corpus: bool
    execution_allowed: bool
    alerts_allowed: bool
    qseries_handoff_allowed: bool
    signals_allowed: bool
    trading_recommendations_allowed: bool
    source_mutation_allowed: bool
    reliability_artifact_persistence_allowed: bool
    report_hash: str
    def to_dict(self) -> Mapping[str, Any]: return _freeze(_canonical(asdict(self)))

class OracleForwardShadowReliabilityDecompositionEngine:
    read_only_corpus=True; execution_allowed=False; alerts_allowed=False; qseries_handoff_allowed=False; signals_allowed=False
    trading_recommendations_allowed=False; source_mutation_allowed=False; reliability_artifact_persistence_allowed=True
    def __init__(self, *, ledger_directory: Path | str = DEFAULT_LEDGER_DIRECTORY, outcome_directory: Path | str = DEFAULT_OUTCOME_DIRECTORY, reliability_directory: Path | str = DEFAULT_RELIABILITY_DIRECTORY, score_bands=DEFAULT_SCORE_BANDS) -> None:
        self._ledger_directory=Path(ledger_directory); self._outcome_directory=Path(outcome_directory); self._reliability_directory=Path(reliability_directory)
        bands=tuple((int(a), int(b)) for a,b in score_bands)
        if not bands or any(a < 0 or b > 100 or a > b for a,b in bands): raise ForwardShadowReliabilityInvariantError("score_bands must be valid 0-100 ranges.")
        self._score_bands=bands
    def _load_outcomes(self) -> list[dict[str, Any]]:
        found=[]
        if not self._outcome_directory.exists(): return found
        for path in sorted(self._outcome_directory.glob("outcomes/*/*.json")):
            payload=json.loads(path.read_text(encoding="utf-8")); digest=payload.pop("outcome_hash", None)
            if digest != outcome_stable_hash(payload): raise ForwardShadowReliabilityInvariantError(f"OIA-010 outcome hash verification failed: {path}")
            if payload.get("schema_version") != "OIA-010" or payload.get("engine_id") != "OIA-010": raise ForwardShadowReliabilityInvariantError(f"Unsupported outcome identity: {path}")
            payload["outcome_hash"]=digest; found.append(payload)
        return found
    def _band(self, probability: Decimal) -> str:
        score=probability*Decimal(100)
        for low, high in self._score_bands:
            if Decimal(low) <= score <= Decimal(high): return f"{low:02d}-{high:03d}"
        return "unbanded"
    @staticmethod
    def _sufficiency(count: int) -> str:
        if count < 30: return "insufficient"
        if count < 100: return "provisional"
        return "established"
    def _component(self, dimension: str, key: str, rows: list[tuple[Decimal, int]]) -> OracleForwardShadowReliabilityComponent:
        n=len(rows); wins=sum(y for _,y in rows); losses=n-wins
        if not n:
            base=brier=reliability=resolution=uncertainty=decomposed=error=Decimal(0); band_count=0
        else:
            base=Decimal(wins)/Decimal(n)
            brier=sum((p-Decimal(y))**2 for p,y in rows)/Decimal(n)
            grouped: dict[str, list[tuple[Decimal,int]]] = {}
            for p,y in rows: grouped.setdefault(self._band(p), []).append((p,y))
            reliability=Decimal(0); resolution=Decimal(0)
            for band_rows in grouped.values():
                nk=len(band_rows); pk=sum(p for p,_ in band_rows)/Decimal(nk); ok=sum(y for _,y in band_rows)/Decimal(nk); weight=Decimal(nk)/Decimal(n)
                reliability += weight*(pk-ok)**2
                resolution += weight*(ok-base)**2
            uncertainty=base*(Decimal(1)-base); decomposed=reliability-resolution+uncertainty; error=abs(brier-decomposed); band_count=len(grouped)
        body={"dimension":dimension,"key":key,"decisive_count":n,"win_count":wins,"loss_count":losses,"base_rate":_fmt(base),"brier_score":_fmt(brier),"reliability":_fmt(reliability),"resolution":_fmt(resolution),"uncertainty":_fmt(uncertainty),"decomposition_brier_score":_fmt(decomposed),"decomposition_error":_fmt(error),"sample_sufficiency":self._sufficiency(n),"probability_band_count":band_count}
        return OracleForwardShadowReliabilityComponent(**body, component_hash=stable_hash(body))
    def analyze(self, *, generated_at: Optional[datetime]=None) -> OracleForwardShadowReliabilityReport:
        anchor=_aware_utc(generated_at or datetime.now(timezone.utc), "generated_at")
        entries=OracleForwardShadowEvaluationLedger(ledger_directory=self._ledger_directory).load_entries(); by_id={e.evaluation_id:e for e in entries}
        outcomes=self._load_outcomes(); seen=set(); joined=[]; duplicates=0; unmatched=0; entry_hashes=set(); outcome_hashes=set()
        for outcome in outcomes:
            if outcome.get("status") != "graded" or outcome.get("grade") not in (WIN, LOSS): continue
            identity=(str(outcome["evaluation_id"]), int(outcome["horizon_seconds"]))
            if identity in seen: duplicates += 1; continue
            seen.add(identity); entry=by_id.get(identity[0])
            if entry is None: unmatched += 1; continue
            if outcome.get("ledger_entry_hash") != entry.entry_hash: raise ForwardShadowReliabilityInvariantError(f"Ledger lineage mismatch for {identity[0]}.")
            probability=_decimal(entry.admission_score, "admission_score")/Decimal(100)
            if probability < 0 or probability > 1: raise ForwardShadowReliabilityInvariantError("admission_score must be between 0 and 100.")
            joined.append((entry,outcome,probability,1 if outcome["grade"]==WIN else 0)); entry_hashes.add(entry.entry_hash); outcome_hashes.add(outcome["outcome_hash"])
        groups: dict[tuple[str,str], list[tuple[Decimal,int]]] = {}
        def add(d,k,p,y): groups.setdefault((d,k),[]).append((p,y))
        for entry,outcome,p,y in joined:
            horizon=str(int(outcome["horizon_seconds"])); family=str(entry.candidate_family); direction=str(entry.research_direction)
            add("overall","all",p,y); add("horizon",horizon,p,y); add("candidate_family_horizon",f"{family}|{horizon}",p,y); add("direction_horizon",f"{direction}|{horizon}",p,y)
        components=tuple(self._component(d,k,groups[(d,k)]) for d,k in sorted(groups))
        body={"schema_version":SCHEMA_VERSION,"engine_id":ENGINE_ID,"generated_at":anchor,"ledger_directory":str(self._ledger_directory),"outcome_directory":str(self._outcome_directory),"reliability_directory":str(self._reliability_directory),"ledger_entry_count":len(entries),"verified_outcome_count":len(outcomes),"joined_decisive_count":len(joined),"unmatched_outcome_count":unmatched,"duplicate_outcome_count":duplicates,"component_count":len(components),"components":components,"source_entry_hashes":tuple(sorted(entry_hashes)),"source_outcome_hashes":tuple(sorted(outcome_hashes)),"read_only_corpus":True,"execution_allowed":False,"alerts_allowed":False,"qseries_handoff_allowed":False,"signals_allowed":False,"trading_recommendations_allowed":False,"source_mutation_allowed":False,"reliability_artifact_persistence_allowed":True}
        report=OracleForwardShadowReliabilityReport(**body, report_hash=stable_hash(body)); self.persist(report); return report
    def persist(self, report: OracleForwardShadowReliabilityReport) -> Path:
        payload=dict(report.to_dict()); digest=payload.pop("report_hash")
        if digest != stable_hash(payload): raise ForwardShadowReliabilityInvariantError("Report hash verification failed.")
        target=self._reliability_directory/"reports"/f"reliability--{digest}.json"; current=self._reliability_directory/"current.json"
        if target.exists() and json.loads(target.read_text(encoding="utf-8")) != dict(report.to_dict()): raise ForwardShadowReliabilityInvariantError("Immutable report collision.")
        if not target.exists(): _atomic(target, report.to_dict())
        _atomic(current, report.to_dict()); return target

def main(argv: Optional[list[str]]=None) -> int:
    parser=argparse.ArgumentParser(description="OIA-013 forward-shadow reliability decomposition engine")
    parser.add_argument("--ledger-directory", default=str(DEFAULT_LEDGER_DIRECTORY)); parser.add_argument("--outcome-directory", default=str(DEFAULT_OUTCOME_DIRECTORY)); parser.add_argument("--reliability-directory", default=str(DEFAULT_RELIABILITY_DIRECTORY))
    args=parser.parse_args(argv); report=OracleForwardShadowReliabilityDecompositionEngine(ledger_directory=args.ledger_directory,outcome_directory=args.outcome_directory,reliability_directory=args.reliability_directory).analyze()
    print(f"[PASS] OIA-013 reliability decomposition complete: decisive={report.joined_decisive_count}, components={report.component_count}, hash={report.report_hash}"); return 0
if __name__ == "__main__": raise SystemExit(main())
