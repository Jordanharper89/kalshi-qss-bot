from __future__ import annotations
from dataclasses import dataclass
import re
READ_ONLY=True; EXECUTION_AUTHORITY=False; PROBABILITY_ENABLED=False

@dataclass(frozen=True,slots=True)
class SportsDetection:
    ticker:str; is_sports:bool; signals:tuple[str,...]; confidence:str

SPORT_STRUCTURE=(
 "both teams to score","wins by over","points scored","runs scored","goals scored",
 "1st half","first half","set betting","game spread","total points","total runs",
 "moneyline","touchdown","home runs","strikeouts","assists","rebounds","yards",
 "round of 16","quarterfinal","semifinal","final","to win","vs","versus"
)
SPORT_SERIES_MARKERS=("NFL","NBA","WNBA","MLB","NHL","NCAAF","NCAAB","ATP","WTA","UFC","MMA","SOCCER","TENNIS","BOXING")

def _fields(m):
    return " ".join(str(m.get(k,"") or "") for k in (
      "ticker","event_ticker","series_ticker","title","subtitle","yes_sub_title","no_sub_title","rules_primary","rules_secondary"
    ))
def _hit(text,phrase):
    return bool(re.search(r"(?<![a-z0-9])"+re.escape(phrase.lower())+r"(?![a-z0-9])",text.lower()))
def detect_sports_market(m):
    text=_fields(m); upper=text.upper(); sig=[]
    for x in SPORT_STRUCTURE:
        if _hit(text,x): sig.append("structure:"+x)
    for x in SPORT_SERIES_MARKERS:
        if re.search(r"(?<![A-Z0-9])"+re.escape(x)+r"(?![A-Z0-9])",upper): sig.append("series:"+x)
    # Cross-category shards often contain comma-separated yes/no legs. Sports structure within a leg is valid evidence.
    yesno=len(re.findall(r"(?<![a-z])(yes|no)(?![a-z])",text.lower()))
    if yesno>=2 and any(k in text.lower() for k in (" points"," runs"," score"," wins by"," vs "," versus ")):
        sig.append("multi_leg_sports_structure")
    sig=tuple(sorted(set(sig)))
    return SportsDetection(str(m.get("ticker","")),bool(sig),sig,"HIGH" if len(sig)>=2 else ("MEDIUM" if sig else "NONE"))
