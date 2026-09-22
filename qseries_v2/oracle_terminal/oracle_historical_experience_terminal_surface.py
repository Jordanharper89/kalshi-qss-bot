from __future__ import annotations
import re
from dataclasses import dataclass
from pathlib import Path
from .oracle_historical_experience_read_model import load_historical_experience_read_model,verify_historical_experience_read_model
from .oracle_live_market_experience_ranker import rank_live_markets_by_experience
from .oracle_historical_ticker_profile import build_historical_ticker_profile
OHE_004_BUILD_ID="OHE-004";OHE_004_REVISION="OHE_004_TRADER_HISTORICAL_EXPERIENCE_TERMINAL_SURFACE_V1"
_QUERY_TOKENS=("learned experience","historical experience","historical setup","historically supported","what markets do you understand","what markets does oracle understand","understand best","rank live markets by learned","rank markets by learned","what has oracle learned","what have you learned about","historical knowledge")
@dataclass(frozen=True)
class HistoricalExperienceTerminalResult:
    query:str;intent:str;lines:tuple;learner_state_hash:str;read_only:bool=True;execution_authority:bool=False
def is_historical_experience_query(query):
    q=" ".join(str(query).lower().split());return bool(q) and any(t in q for t in _QUERY_TOKENS)
def _ticker_from_query(query):
    for token in re.findall(r"[A-Za-z0-9_.:-]+",str(query)):
        u=token.upper().strip(".,:;!?")
        if u.startswith("KX") and len(u)>=4:return u
    return None
def _ranking_lines(model,limit=10):
    rows=rank_live_markets_by_experience(model,limit);lines=["="*72,"ORACLE HISTORICAL EXPERIENCE — LIVE RANKING","READ-ONLY | EXPERIENCE RANKING, NOT A TRADE SIGNAL",f"LEARNER: cycles={model.cycles} outcomes={model.outcomes_learned} learned_records={model.learned_records}",f"LIVE REASONING: markets={model.markets_reasoned} usable={model.experience_contexts} withheld={model.withheld_contexts} blind={model.blind_contexts}",f"LINEAGE CURRENT: {'YES' if model.lineage_current else 'NO — reasoning snapshot trails learner state'}","-"*72]
    if not rows:return tuple(lines+["No current historical-experience contexts are available.","="*72])
    for r in rows:
        lines += [f"{r.rank}. {r.market_ticker}",f"   maturity={r.maturity} experience={'AVAILABLE' if r.experience_available else 'WITHHELD/BLIND'}",f"   learned_series_records={r.series_learned_records} reliability={r.reliability:.3f}",f"   regime={r.regime_id or '(none)'}",f"   why={r.rank_reason}",f"   experience_index={r.experience_score:.2f} (ranking index only)"]
    return tuple(lines+["-"*72,"No order placement. No execution authority.","="*72])
def _profile_lines(model,ticker):
    p=build_historical_ticker_profile(model,ticker)
    return ("="*72,"ORACLE HISTORICAL EXPERIENCE — MARKET PROFILE","READ-ONLY | HISTORICAL KNOWLEDGE, NOT A TRADE SIGNAL",f"TICKER: {p.ticker}",f"FAMILY: {p.family}",f"EXACT LEARNED RECORDS: {p.exact_learned_records}",f"FAMILY LEARNED RECORDS: {p.family_learned_records}",f"CURRENT CONTEXT FOUND: {'YES' if p.current_context_found else 'NO'}",f"MATURITY: {p.maturity}",f"EXPERIENCE AVAILABLE NOW: {'YES' if p.experience_available else 'NO'}",f"RELIABILITY: {p.reliability:.3f}",f"REGIME: {p.regime_id or '(none)'}",f"REASON: {p.reason}",f"LINEAGE CURRENT: {'YES' if p.lineage_current else 'NO'}","No order placement. No execution authority.","="*72)
def answer_historical_experience_query(root,query,limit=10):
    model=load_historical_experience_read_model(Path(root));verify_historical_experience_read_model(model);ticker=_ticker_from_query(query)
    if ticker:intent="ticker_profile";lines=_profile_lines(model,ticker)
    else:intent="live_ranking";lines=_ranking_lines(model,limit)
    return HistoricalExperienceTerminalResult(str(query),intent,lines,model.learner_state_hash,True,False)
