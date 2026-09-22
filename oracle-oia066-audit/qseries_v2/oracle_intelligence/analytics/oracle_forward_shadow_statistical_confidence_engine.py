"""
OIA-014
Oracle Forward Shadow Statistical Confidence Engine

Computes deterministic Wilson confidence intervals and evidence sufficiency for
immutable decisive forward-shadow outcomes. Research analytics only; no signals,
alerts, recommendations, Q Series handoffs, or execution.
"""
from __future__ import annotations

import argparse, hashlib, json, math, os, tempfile
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation, ROUND_HALF_EVEN
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping

from .oracle_forward_shadow_evaluation_ledger import DEFAULT_LEDGER_DIRECTORY, OracleForwardShadowEvaluationLedger
from .oracle_forward_shadow_outcome_evaluator import DEFAULT_OUTCOME_DIRECTORY, LOSS, WIN, stable_hash as outcome_stable_hash

SCHEMA_VERSION = "OIA-014"
ENGINE_ID = "OIA-014"
READ_ONLY_CORPUS = True
EXECUTION_ALLOWED = False
ALERTS_ALLOWED = False
QSERIES_HANDOFF_ALLOWED = False
SIGNALS_ALLOWED = False
TRADING_RECOMMENDATIONS_ALLOWED = False
SOURCE_MUTATION_ALLOWED = False
CONFIDENCE_ARTIFACT_PERSISTENCE_ALLOWED = True
DEFAULT_CONFIDENCE_DIRECTORY = Path("runtime") / "oracle_intelligence" / "forward_shadow_confidence"
DEFAULT_CONFIDENCE_LEVEL = Decimal("0.95")
DEFAULT_Z_SCORE = Decimal("1.959963984540054")
_QUANT = Decimal("0.00000001")

class ForwardShadowConfidenceError(RuntimeError): pass
class ForwardShadowConfidenceInvariantError(ForwardShadowConfidenceError): pass

def _aware_utc(value: datetime, name: str) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise ForwardShadowConfidenceInvariantError(f"{name} must be timezone-aware.")
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
    except (InvalidOperation, ValueError, TypeError) as exc: raise ForwardShadowConfidenceInvariantError(f"{name} must be a finite decimal.") from exc
    if not result.is_finite(): raise ForwardShadowConfidenceInvariantError(f"{name} must be a finite decimal.")
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
class OracleForwardShadowConfidenceComponent:
    dimension: str
    key: str
    decisive_count: int
    win_count: int
    loss_count: int
    observed_win_rate: str
    confidence_level: str
    lower_bound: str
    upper_bound: str
    interval_width: str
    margin_of_error: str
    evidence_sufficiency: str
    statistically_above_chance: bool
    statistically_below_chance: bool
    component_hash: str
    def to_dict(self) -> Mapping[str, Any]: return _freeze(_canonical(asdict(self)))

@dataclass(frozen=True)
class OracleForwardShadowConfidenceReport:
    schema_version: str
    engine_id: str
    generated_at: datetime
    ledger_directory: str
    outcome_directory: str
    confidence_directory: str
    ledger_entry_count: int
    verified_outcome_count: int
    joined_decisive_count: int
    unmatched_outcome_count: int
    duplicate_outcome_count: int
    component_count: int
    confidence_level: str
    components: tuple[OracleForwardShadowConfidenceComponent, ...]
    source_entry_hashes: tuple[str, ...]
    source_outcome_hashes: tuple[str, ...]
    read_only_corpus: bool
    execution_allowed: bool
    alerts_allowed: bool
    qseries_handoff_allowed: bool
    signals_allowed: bool
    trading_recommendations_allowed: bool
    source_mutation_allowed: bool
    confidence_artifact_persistence_allowed: bool
    report_hash: str
    def to_dict(self) -> Mapping[str, Any]: return _freeze(_canonical(asdict(self)))

class OracleForwardShadowStatisticalConfidenceEngine:
    read_only_corpus=True; execution_allowed=False; alerts_allowed=False; qseries_handoff_allowed=False; signals_allowed=False
    trading_recommendations_allowed=False; source_mutation_allowed=False; confidence_artifact_persistence_allowed=True
    def __init__(self, *, ledger_directory: Path | str = DEFAULT_LEDGER_DIRECTORY, outcome_directory: Path | str = DEFAULT_OUTCOME_DIRECTORY, confidence_directory: Path | str = DEFAULT_CONFIDENCE_DIRECTORY, confidence_level: Decimal | str = DEFAULT_CONFIDENCE_LEVEL, z_score: Decimal | str = DEFAULT_Z_SCORE) -> None:
        self._ledger_directory=Path(ledger_directory); self._outcome_directory=Path(outcome_directory); self._confidence_directory=Path(confidence_directory)
        self._confidence_level=_decimal(confidence_level, "confidence_level"); self._z=_decimal(z_score, "z_score")
        if not Decimal(0) < self._confidence_level < Decimal(1): raise ForwardShadowConfidenceInvariantError("confidence_level must be between zero and one.")
        if self._z <= 0: raise ForwardShadowConfidenceInvariantError("z_score must be positive.")
    def _load_outcomes(self) -> list[dict[str, Any]]:
        found=[]
        if not self._outcome_directory.exists(): return found
        for path in sorted(self._outcome_directory.glob("outcomes/*/*.json")):
            payload=json.loads(path.read_text(encoding="utf-8")); digest=payload.pop("outcome_hash", None)
            if digest != outcome_stable_hash(payload): raise ForwardShadowConfidenceInvariantError(f"OIA-010 outcome hash verification failed: {path}")
            if payload.get("schema_version") != "OIA-010" or payload.get("engine_id") != "OIA-010": raise ForwardShadowConfidenceInvariantError(f"Unsupported outcome identity: {path}")
            payload["outcome_hash"]=digest; found.append(payload)
        return found
    @staticmethod
    def _sufficiency(count: int, width: Decimal) -> str:
        if count < 30: return "insufficient"
        if count < 100 or width > Decimal("0.25"): return "provisional"
        if count < 400 or width > Decimal("0.12"): return "established"
        return "strong"
    def _component(self, dimension: str, key: str, rows: list[int]) -> OracleForwardShadowConfidenceComponent:
        n=len(rows); wins=sum(rows); losses=n-wins
        if n == 0:
            rate=lower=upper=width=margin=Decimal(0)
        else:
            dn=Decimal(n); rate=Decimal(wins)/dn; z2=self._z*self._z
            denominator=Decimal(1)+z2/dn
            center=(rate+z2/(Decimal(2)*dn))/denominator
            root=Decimal(str(math.sqrt(float((rate*(Decimal(1)-rate)+z2/(Decimal(4)*dn))/dn))))
            half=(self._z*root)/denominator
            lower=max(Decimal(0), center-half); upper=min(Decimal(1), center+half)
            width=upper-lower; margin=width/Decimal(2)
        body={"dimension":dimension,"key":key,"decisive_count":n,"win_count":wins,"loss_count":losses,"observed_win_rate":_fmt(rate),"confidence_level":_fmt(self._confidence_level),"lower_bound":_fmt(lower),"upper_bound":_fmt(upper),"interval_width":_fmt(width),"margin_of_error":_fmt(margin),"evidence_sufficiency":self._sufficiency(n,width),"statistically_above_chance":bool(n and lower > Decimal("0.5")),"statistically_below_chance":bool(n and upper < Decimal("0.5"))}
        return OracleForwardShadowConfidenceComponent(**body, component_hash=stable_hash(body))
    def analyze(self, *, generated_at: datetime | None = None, persist: bool = True) -> OracleForwardShadowConfidenceReport:
        generated_at=_aware_utc(generated_at or datetime.now(timezone.utc), "generated_at")
        ledger=OracleForwardShadowEvaluationLedger(ledger_directory=self._ledger_directory)
        entries=ledger.load_entries(); entry_map={e.evaluation_id:e for e in entries}
        outcomes=self._load_outcomes(); seen=set(); joined=[]; unmatched=0; duplicates=0; outcome_hashes=[]
        for outcome in outcomes:
            identity=(str(outcome.get("evaluation_id")), int(outcome.get("horizon_seconds",0)))
            if identity in seen: duplicates += 1; continue
            seen.add(identity)
            if outcome.get("grade") not in (WIN, LOSS): continue
            entry=entry_map.get(identity[0])
            if entry is None or outcome.get("ledger_entry_hash") != entry.entry_hash: unmatched += 1; continue
            joined.append((entry,outcome,1 if outcome["grade"]==WIN else 0)); outcome_hashes.append(outcome["outcome_hash"])
        groups: dict[tuple[str,str], list[int]] = {("overall","all"):[]}
        for entry,outcome,y in joined:
            h=str(outcome["horizon_seconds"]); groups[("overall","all")].append(y)
            groups.setdefault(("horizon",h),[]).append(y)
            groups.setdefault(("candidate_family_horizon",f"{entry.candidate_family}|{h}"),[]).append(y)
            groups.setdefault(("research_direction_horizon",f"{entry.research_direction}|{h}"),[]).append(y)
            score=int(Decimal(str(entry.admission_score))); band=f"{(score//10)*10:02d}-{min(100,(score//10)*10+9):03d}"
            groups.setdefault(("admission_score_band_horizon",f"{band}|{h}"),[]).append(y)
        components=tuple(self._component(d,k,groups[(d,k)]) for d,k in sorted(groups))
        body={"schema_version":SCHEMA_VERSION,"engine_id":ENGINE_ID,"generated_at":generated_at,"ledger_directory":str(self._ledger_directory),"outcome_directory":str(self._outcome_directory),"confidence_directory":str(self._confidence_directory),"ledger_entry_count":len(entries),"verified_outcome_count":len(outcomes),"joined_decisive_count":len(joined),"unmatched_outcome_count":unmatched,"duplicate_outcome_count":duplicates,"component_count":len(components),"confidence_level":_fmt(self._confidence_level),"components":components,"source_entry_hashes":tuple(sorted(e.entry_hash for e in entries)),"source_outcome_hashes":tuple(sorted(outcome_hashes)),"read_only_corpus":True,"execution_allowed":False,"alerts_allowed":False,"qseries_handoff_allowed":False,"signals_allowed":False,"trading_recommendations_allowed":False,"source_mutation_allowed":False,"confidence_artifact_persistence_allowed":True}
        report=OracleForwardShadowConfidenceReport(**body, report_hash=stable_hash(body))
        if persist:
            payload=report.to_dict(); _atomic(self._confidence_directory/f"confidence--{report.report_hash}.json", payload); _atomic(self._confidence_directory/"current.json", payload)
        return report

def main(argv=None) -> int:
    parser=argparse.ArgumentParser(description="OIA-014 forward-shadow statistical confidence engine")
    parser.add_argument("--ledger-directory", default=str(DEFAULT_LEDGER_DIRECTORY)); parser.add_argument("--outcome-directory", default=str(DEFAULT_OUTCOME_DIRECTORY)); parser.add_argument("--confidence-directory", default=str(DEFAULT_CONFIDENCE_DIRECTORY)); parser.add_argument("--no-persist", action="store_true")
    args=parser.parse_args(argv)
    report=OracleForwardShadowStatisticalConfidenceEngine(ledger_directory=args.ledger_directory,outcome_directory=args.outcome_directory,confidence_directory=args.confidence_directory).analyze(persist=not args.no_persist)
    print(json.dumps(report.to_dict(),sort_keys=True,indent=2)); return 0
if __name__ == "__main__": raise SystemExit(main())
