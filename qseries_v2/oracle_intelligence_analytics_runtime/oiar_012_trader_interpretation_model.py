from dataclasses import dataclass
from .oiar_011_market_identity_translator import translate_market_identity
OIAR_012_BUILD_ID="OIAR-012"
@dataclass(frozen=True)
class TraderInterpretation:
 market_id:str;market_name:str;category:str;historical_strength:str;live_evidence:str;direction:str;setup_quality:str;risk:str;takeaway:str;read_only:bool=True;execution_authority:bool=False
def interpret_trader_row(r):
 i=translate_market_identity(r.market_id);m=str(r.maturity).upper();rel=float(r.reliability or 0);n=int(r.history_rows or 0);u=float(r.usefulness_score or 0)
 h="STRONG" if m=="PROVEN" and rel>=.60 else "MODERATE" if m in ("PROVEN","MATURE") or rel>=.50 else "LIMITED"
 l="STRONG" if n>=20 and u>=50 else "DEVELOPING" if n>=8 or u>=25 else "WEAK"
 adm=str(r.admission_status).lower()=="admitted";cand=str(r.candidate_family).lower()!="none"
 q="ACTIONABLE_RESEARCH" if adm else "FORMING" if cand else "NO_CONFIRMED_SETUP"
 t="WORTH WATCHING NOW" if adm else "WATCH - SETUP IS FORMING" if cand else "NO EDGE RIGHT NOW"
 return TraderInterpretation(r.market_id,i.display_name,i.category,h,l,str(r.research_direction or "neutral").upper(),q,"HIGH" if l=="WEAK" else "MODERATE",t)
