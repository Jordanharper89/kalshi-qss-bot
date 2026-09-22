"""
OIA-012
Oracle Forward Shadow Admission Score Calibration Analyzer

Joins immutable OIA-009 entry records to immutable OIA-010 graded outcomes and
measures how admission scores relate to realized fixed-horizon results. This is
research calibration only; it creates no signals, alerts, recommendations, or execution.
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
from .oracle_forward_shadow_outcome_evaluator import DEFAULT_OUTCOME_DIRECTORY, FLAT, GRADED, LOSS, WIN, stable_hash as outcome_stable_hash

SCHEMA_VERSION="OIA-012"
ENGINE_ID="OIA-012"
READ_ONLY_CORPUS=True
EXECUTION_ALLOWED=False
ALERTS_ALLOWED=False
QSERIES_HANDOFF_ALLOWED=False
SIGNALS_ALLOWED=False
TRADING_RECOMMENDATIONS_ALLOWED=False
SOURCE_MUTATION_ALLOWED=False
CALIBRATION_ARTIFACT_PERSISTENCE_ALLOWED=True
DEFAULT_CALIBRATION_DIRECTORY=Path("runtime")/"oracle_intelligence"/"forward_shadow_calibration"
DEFAULT_SCORE_BANDS=((0,59),(60,69),(70,79),(80,89),(90,100))
_QUANT=Decimal("0.00000001")

class ForwardShadowCalibrationError(RuntimeError): pass
class ForwardShadowCalibrationInvariantError(ForwardShadowCalibrationError): pass

def _aware_utc(v:datetime,n:str)->datetime:
    if not isinstance(v,datetime) or v.tzinfo is None or v.utcoffset() is None: raise ForwardShadowCalibrationInvariantError(f"{n} must be timezone-aware.")
    return v.astimezone(timezone.utc)

def _canonical(v:Any)->Any:
    if is_dataclass(v): return _canonical(asdict(v))
    if isinstance(v,Mapping): return {str(k):_canonical(x) for k,x in v.items()}
    if isinstance(v,(list,tuple)): return [_canonical(x) for x in v]
    if isinstance(v,datetime): return _aware_utc(v,"datetime").isoformat()
    if isinstance(v,Decimal): return format(v,"f")
    return v

def stable_hash(v:Any)->str:
    return hashlib.sha256(json.dumps(_canonical(v),sort_keys=True,separators=(",",":"),ensure_ascii=False,allow_nan=False).encode()).hexdigest()

def _freeze(v:Mapping[str,Any])->Mapping[str,Any]: return MappingProxyType(dict(v))
def _decimal(v:Any,n:str)->Decimal:
    try: d=Decimal(str(v))
    except (InvalidOperation,ValueError,TypeError) as e: raise ForwardShadowCalibrationInvariantError(f"{n} must be a finite decimal.") from e
    if not d.is_finite(): raise ForwardShadowCalibrationInvariantError(f"{n} must be a finite decimal.")
    return d

def _fmt(v:Decimal)->str: return format(v.quantize(_QUANT,rounding=ROUND_HALF_EVEN),"f")
def _ratio(a:int,b:int)->str: return _fmt(Decimal(a)/Decimal(b)) if b else "0.00000000"
def _atomic(path:Path,payload:Mapping[str,Any])->None:
    path.parent.mkdir(parents=True,exist_ok=True); data=json.dumps(_canonical(payload),sort_keys=True,indent=2,ensure_ascii=False)+"\n"
    h=tempfile.NamedTemporaryFile("w",encoding="utf-8",newline="\n",delete=False,dir=str(path.parent),prefix=f".{path.name}.",suffix=".tmp"); t=Path(h.name)
    try:
        with h: h.write(data); h.flush(); os.fsync(h.fileno())
        os.replace(t,path)
    finally:
        if t.exists(): t.unlink()

@dataclass(frozen=True)
class OracleForwardShadowCalibrationBucket:
    dimension:str; key:str; graded_count:int; decisive_count:int; win_count:int; loss_count:int; flat_count:int
    mean_admission_score:str; mean_score_probability:str; empirical_win_rate:str; calibration_error:str; brier_score:str; bucket_hash:str
    def to_dict(self)->Mapping[str,Any]: return _freeze(_canonical(asdict(self)))

@dataclass(frozen=True)
class OracleForwardShadowCalibrationReport:
    schema_version:str; engine_id:str; generated_at:datetime; ledger_directory:str; outcome_directory:str; calibration_directory:str
    ledger_entry_count:int; verified_outcome_count:int; joined_outcome_count:int; unmatched_outcome_count:int; duplicate_outcome_count:int
    bucket_count:int; buckets:tuple[OracleForwardShadowCalibrationBucket,...]; source_entry_hashes:tuple[str,...]; source_outcome_hashes:tuple[str,...]
    read_only_corpus:bool; execution_allowed:bool; alerts_allowed:bool; qseries_handoff_allowed:bool; signals_allowed:bool
    trading_recommendations_allowed:bool; source_mutation_allowed:bool; calibration_artifact_persistence_allowed:bool; report_hash:str
    def to_dict(self)->Mapping[str,Any]: return _freeze(_canonical(asdict(self)))

class OracleForwardShadowCalibrationAnalyzer:
    read_only_corpus=True; execution_allowed=False; alerts_allowed=False; qseries_handoff_allowed=False; signals_allowed=False
    trading_recommendations_allowed=False; source_mutation_allowed=False; calibration_artifact_persistence_allowed=True
    def __init__(self,*,ledger_directory:Path|str=DEFAULT_LEDGER_DIRECTORY,outcome_directory:Path|str=DEFAULT_OUTCOME_DIRECTORY,calibration_directory:Path|str=DEFAULT_CALIBRATION_DIRECTORY,score_bands=DEFAULT_SCORE_BANDS)->None:
        self._ledger_directory=Path(ledger_directory); self._outcome_directory=Path(outcome_directory); self._calibration_directory=Path(calibration_directory)
        bands=tuple((int(a),int(b)) for a,b in score_bands)
        if not bands or any(a<0 or b>100 or a>b for a,b in bands): raise ForwardShadowCalibrationInvariantError("score_bands must be valid 0-100 ranges.")
        self._score_bands=bands
    def _load_outcomes(self):
        found=[]
        if not self._outcome_directory.exists(): return found
        for path in sorted(self._outcome_directory.glob("outcomes/*/*.json")):
            payload=json.loads(path.read_text(encoding="utf-8"))
            digest=payload.pop("outcome_hash",None)
            if digest!=outcome_stable_hash(payload): raise ForwardShadowCalibrationInvariantError(f"OIA-010 outcome hash verification failed: {path}")
            if payload.get("schema_version")!="OIA-010" or payload.get("engine_id")!="OIA-010": raise ForwardShadowCalibrationInvariantError(f"Unsupported outcome identity: {path}")
            payload["outcome_hash"]=digest; found.append(payload)
        return found
    def _band(self,score:Decimal)->str:
        for a,b in self._score_bands:
            if Decimal(a)<=score<=Decimal(b): return f"{a:02d}-{b:03d}"
        return "unbanded"
    def _bucket(self,dimension:str,key:str,rows:list[tuple[Decimal,str]])->OracleForwardShadowCalibrationBucket:
        graded=len(rows); decisive=[(s,g) for s,g in rows if g in (WIN,LOSS)]; wins=sum(g==WIN for _,g in decisive); losses=sum(g==LOSS for _,g in decisive); flats=sum(g==FLAT for _,g in rows)
        mean_score=(sum((s for s,_ in rows),Decimal(0))/Decimal(graded)) if graded else Decimal(0); mean_prob=mean_score/Decimal(100)
        empirical=Decimal(wins)/Decimal(len(decisive)) if decisive else Decimal(0)
        error=abs(mean_prob-empirical) if decisive else Decimal(0)
        brier=(sum(((s/Decimal(100))-(Decimal(1) if g==WIN else Decimal(0)))**2 for s,g in decisive)/Decimal(len(decisive))) if decisive else Decimal(0)
        body={"dimension":dimension,"key":key,"graded_count":graded,"decisive_count":len(decisive),"win_count":wins,"loss_count":losses,"flat_count":flats,"mean_admission_score":_fmt(mean_score),"mean_score_probability":_fmt(mean_prob),"empirical_win_rate":_fmt(empirical),"calibration_error":_fmt(error),"brier_score":_fmt(brier)}
        return OracleForwardShadowCalibrationBucket(**body,bucket_hash=stable_hash(body))
    def analyze(self,*,generated_at:Optional[datetime]=None)->OracleForwardShadowCalibrationReport:
        anchor=_aware_utc(generated_at or datetime.now(timezone.utc),"generated_at")
        entries=OracleForwardShadowEvaluationLedger(ledger_directory=self._ledger_directory).load_entries(); by_id={e.evaluation_id:e for e in entries}
        outcomes=self._load_outcomes(); seen=set(); joined=[]; duplicates=0; unmatched=0
        entry_hashes=set(); outcome_hashes=set()
        for o in outcomes:
            if o.get("status")!=GRADED or o.get("grade") not in (WIN,LOSS,FLAT): continue
            identity=(str(o["evaluation_id"]),int(o["horizon_seconds"]))
            if identity in seen: duplicates+=1; continue
            seen.add(identity); e=by_id.get(identity[0])
            if e is None: unmatched+=1; continue
            if o.get("ledger_entry_hash")!=e.entry_hash: raise ForwardShadowCalibrationInvariantError(f"Ledger lineage mismatch for {identity[0]}.")
            score=_decimal(e.admission_score,"admission_score")
            if score<0 or score>100: raise ForwardShadowCalibrationInvariantError("admission_score must be between 0 and 100.")
            joined.append((e,o,score)); entry_hashes.add(e.entry_hash); outcome_hashes.add(o["outcome_hash"])
        groups={}
        def add(d,k,s,g): groups.setdefault((d,k),[]).append((s,g))
        for e,o,s in joined:
            g=o["grade"]; h=str(int(o["horizon_seconds"]))
            add("overall","all",s,g); add("horizon",h,s,g); add("score_band_horizon",f"{self._band(s)}|{h}",s,g); add("family_horizon",f"{e.candidate_family}|{h}",s,g)
        buckets=tuple(self._bucket(d,k,groups[(d,k)]) for d,k in sorted(groups))
        body={"schema_version":SCHEMA_VERSION,"engine_id":ENGINE_ID,"generated_at":anchor,"ledger_directory":str(self._ledger_directory),"outcome_directory":str(self._outcome_directory),"calibration_directory":str(self._calibration_directory),"ledger_entry_count":len(entries),"verified_outcome_count":len(outcomes),"joined_outcome_count":len(joined),"unmatched_outcome_count":unmatched,"duplicate_outcome_count":duplicates,"bucket_count":len(buckets),"buckets":buckets,"source_entry_hashes":tuple(sorted(entry_hashes)),"source_outcome_hashes":tuple(sorted(outcome_hashes)),"read_only_corpus":True,"execution_allowed":False,"alerts_allowed":False,"qseries_handoff_allowed":False,"signals_allowed":False,"trading_recommendations_allowed":False,"source_mutation_allowed":False,"calibration_artifact_persistence_allowed":True}
        report=OracleForwardShadowCalibrationReport(**body,report_hash=stable_hash(body)); _atomic(self._calibration_directory/"current.json",report.to_dict()); _atomic(self._calibration_directory/f"calibration--{report.report_hash}.json",report.to_dict()); return report

def format_report(r):
    lines=["="*110,"ORACLE FORWARD SHADOW ADMISSION SCORE CALIBRATION REPORT","="*110,f"Generated at: {r.generated_at.isoformat()}",f"Joined outcomes: {r.joined_outcome_count} | unmatched: {r.unmatched_outcome_count} | buckets: {r.bucket_count}"]
    for b in r.buckets: lines.append(f"{b.dimension:<24} {b.key:<35} n={b.graded_count:<5} decisive={b.decisive_count:<5} score={b.mean_admission_score} win_rate={b.empirical_win_rate} error={b.calibration_error} brier={b.brier_score}")
    lines.append("Research calibration only. No signals, alerts, recommendations, or execution."); return "\n".join(lines)

def main()->int:
    p=argparse.ArgumentParser(); p.add_argument("--ledger-directory",default=str(DEFAULT_LEDGER_DIRECTORY)); p.add_argument("--outcome-directory",default=str(DEFAULT_OUTCOME_DIRECTORY)); p.add_argument("--calibration-directory",default=str(DEFAULT_CALIBRATION_DIRECTORY)); p.add_argument("--json",action="store_true"); a=p.parse_args()
    r=OracleForwardShadowCalibrationAnalyzer(ledger_directory=a.ledger_directory,outcome_directory=a.outcome_directory,calibration_directory=a.calibration_directory).analyze()
    print(json.dumps(dict(r.to_dict()),indent=2,sort_keys=True) if a.json else format_report(r)); return 0
if __name__=="__main__": raise SystemExit(main())
