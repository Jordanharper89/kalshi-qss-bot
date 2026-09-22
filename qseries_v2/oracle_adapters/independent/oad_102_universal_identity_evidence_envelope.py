from __future__ import annotations
from dataclasses import dataclass
import re

READ_ONLY=True
EXECUTION_AUTHORITY=False
PROBABILITY_ENABLED=False

@dataclass(frozen=True, slots=True)
class IdentityEvidence:
    scope: str
    evidence_type: str
    value: str
    strength: int
    source_text: str

@dataclass(frozen=True, slots=True)
class IdentityEnvelope:
    parent_ticker: str
    leg_index: int
    leg_text: str
    local_evidence: tuple[IdentityEvidence,...]
    parent_evidence: tuple[IdentityEvidence,...]
    sibling_evidence: tuple[IdentityEvidence,...]

def _ev(scope, typ, value, strength, text):
    return IdentityEvidence(scope,typ,value,strength,str(text or ""))

def _local(text):
    text=str(text or "")
    low=text.lower()
    out=[]
    checks=[
      ("sport","baseball",95,(r"\binnings?\b",r"\bstrikeouts?\b",r"\bhome runs?\b",r"\brbi\b")),
      ("sport","soccer",95,(r"\bboth teams to score\b",r"\bclean sheet\b",r"\bgoals?\b")),
      ("sport","tennis",95,(r"\bsets?\b",r"\baces?\b",r"\bdouble faults?\b",r"\bwins 2-1\b",r"\bwins 3-0\b")),
      ("sport","combat",98,(r"\bsubmission\b",r"\bko/tko\b",r"\bdecision\b",r"\bufc\b",r"\bmma\b")),
      ("sport","esports",98,(r"\besports?\b",r"\bvalorant\b",r"\bcounter-strike\b")),
      ("sport","hockey",98,(r"\bnhl\b",r"\bshots on goal\b",r"\bpower play\b")),
      ("sport","basketball",95,(r"\brebounds?\b",r"\bassists?\b",r"\bthree pointers?\b",r"\bnba\b",r"\bwnba\b")),
      ("sport","football",95,(r"\btouchdowns?\b",r"\bpassing yards?\b",r"\brushing yards?\b",r"\bnfl\b")),
    ]
    for typ,val,strength,pats in checks:
        if any(re.search(p,low,re.I) for p in pats):
            out.append(_ev("local",typ,val,strength,text))
    if re.search(r":\s*\d+(?:\.\d+)?\+(?=\s|$|[,;/)])",text):
        out.append(_ev("local","market_type","player_prop",90,text))
    if "/" in text and len(text.split("/"))==2:
        out.append(_ev("local","market_type","participant_pair",85,text))
    if re.fullmatch(r"[A-Za-zÀ-ÿ0-9 .'\-/&()]+",text.strip()) and 1<=len(text.split())<=7:
        out.append(_ev("local","entity_shape","named_entity",35,text))
    return tuple(out)

def _context_text(market):
    return " ".join(str(market.get(k,"") or "") for k in (
        "ticker","event_ticker","series_ticker","rules_primary","rules_secondary"
    ))

def build_identity_envelopes(market, legs):
    parent=_context_text(market)
    parent_ev=_local(parent)
    rows=[]
    for leg in legs:
        sib=[]
        for other in legs:
            if other.leg_index != leg.leg_index:
                for e in _local(other.text):
                    sib.append(_ev("sibling",e.evidence_type,e.value,min(e.strength,55),other.text))
        rows.append(IdentityEnvelope(
            str(leg.parent_ticker), int(leg.leg_index), str(leg.text),
            _local(leg.text),
            tuple(_ev("parent",e.evidence_type,e.value,min(e.strength,75),parent) for e in parent_ev),
            tuple(sib),
        ))
    return tuple(rows)
