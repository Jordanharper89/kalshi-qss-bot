
from __future__ import annotations
from pathlib import Path
from .oiar_025_fast_persisted_trader_brief_read_model import read_fast_trader_brief
from .oiar_027_trader_intent_classifier import classify_trader_intent
from .oiar_029_trader_session_context import TraderSessionContext,apply_intent
from .oiar_030_concise_trader_response_policy import render_concise
OIAR_031_BUILD_ID="OIAR-031"
OIAR_031_REVISION="OIAR_031_UNIFIED_TRADER_CONVERSATION_CUTOVER_V1"
_CONTEXT=TraderSessionContext()
def bind_unified_trader_conversation(base_module,root=None):
    if getattr(base_module,"_oiar031_bound",False):return base_module
    original=base_module.display_query;active=Path(root or base_module.repository_root()).resolve()
    def display_query(query,*,session=None,root=None,builder=None,write=print):
        canonical=base_module.normalize_query(query);intent=classify_trader_intent(canonical)
        if intent.route=="trader_brief":
            use=Path(root or active).resolve();apply_intent(_CONTEXT,intent)
            x=read_fast_trader_brief(use,50)
            for line in render_concise(x.markets,intent,2):write(line)
            return None
        kwargs={"session":session,"root":Path(root or active).resolve(),"write":write}
        if builder is not None:kwargs["builder"]=builder
        return original(canonical,**kwargs)
    base_module.display_query=display_query;base_module._oiar031_bound=True
    return base_module
