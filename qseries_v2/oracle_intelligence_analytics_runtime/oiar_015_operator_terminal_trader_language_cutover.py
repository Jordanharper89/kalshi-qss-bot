from pathlib import Path
from .oiar_009_fast_terminal_read_adapter import read_fast_trader_intelligence
from .oiar_011_market_identity_translator import translate_market_identity
from .oiar_013_trader_brief_renderer import render_trader_brief
from .oiar_014_natural_trader_question_router import is_trader_brief_query,trader_query_filter
OIAR_015_BUILD_ID="OIAR-015"
def bind_trader_language(base,root=None):
 if getattr(base,"_oiar015_bound",False):return base
 old=base.display_query;active=Path(root or base.repository_root()).resolve()
 def display_query(query,*,session=None,root=None,builder=None,write=print):
  q=base.normalize_query(query);use=Path(root or active).resolve()
  if is_trader_brief_query(q):
   s=read_fast_trader_intelligence(use,20);rows=s.rows;f=trader_query_filter(q)
   if f:rows=tuple(r for r in rows if translate_market_identity(r.market_id).category==f)
   for line in render_trader_brief(rows,s.freshness_status,s.age_seconds,5):write(line)
   return s
  kw={"session":session,"root":use,"write":write}
  if builder is not None:kw["builder"]=builder
  return old(q,**kw)
 base.display_query=display_query;base._oiar015_bound=True;return base
