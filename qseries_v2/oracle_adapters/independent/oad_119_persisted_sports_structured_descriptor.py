from __future__ import annotations
from dataclasses import dataclass
from collections.abc import Mapping
import re

READ_ONLY=True
EXECUTION_AUTHORITY=False
PROBABILITY_ENABLED=False

@dataclass(frozen=True, slots=True)
class SportsEvidenceDescriptor:
    observation_id: str
    source_id: str
    sport_family: str
    subject: str
    away_team: str
    home_team: str
    team_pair_key: str
    evidence_type: str
    independent_evidence: bool
    execution_authority: bool=False

def _thaw(v):
    if isinstance(v,Mapping): return {str(k):_thaw(x) for k,x in v.items()}
    if isinstance(v,tuple):
        if all(isinstance(x,tuple) and len(x)==2 for x in v):
            try: return {str(k):_thaw(x) for k,x in v}
            except Exception: pass
        return tuple(_thaw(x) for x in v)
    if isinstance(v,list): return [_thaw(x) for x in v]
    return v

def _norm(v):
    return " ".join(re.findall(r"[a-z0-9]+",str(v or "").lower()))

def descriptor_from_persisted_sports_row(row):
    payload=_thaw(getattr(row,"payload",{}))
    if not isinstance(payload,dict): raise ValueError("canonical sports payload mapping required")
    subject=str(payload.get("subject","")).strip()
    source_id=str(getattr(row,"source_id",""))
    independent=payload.get("independent_evidence") is True
    if not independent or not source_id.startswith("source.independent."):
        raise ValueError("persisted independent sports evidence required")
    parts=subject.split(" at ",1)
    away=parts[0].strip() if len(parts)==2 else ""
    home=parts[1].strip() if len(parts)==2 else ""
    sport="baseball" if ".mlb:game:" in source_id else ("hockey" if ".nhl:game:" in source_id else "UNKNOWN")
    pair="|".join(sorted(x for x in (_norm(away),_norm(home)) if x))
    return SportsEvidenceDescriptor(
        observation_id=str(row.observation_id),
        source_id=source_id,
        sport_family=sport,
        subject=subject,
        away_team=away,
        home_team=home,
        team_pair_key=pair,
        evidence_type="official_game_schedule_state",
        independent_evidence=True,
        execution_authority=False,
    )

def descriptors_from_persisted_sports_rows(rows):
    return tuple(descriptor_from_persisted_sports_row(x) for x in rows)
