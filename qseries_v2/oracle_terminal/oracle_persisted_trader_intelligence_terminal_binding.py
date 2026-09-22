from __future__ import annotations
from pathlib import Path

from qseries_v2.oracle_intelligence_analytics_runtime.oiar_009_fast_terminal_read_adapter import (
    read_fast_trader_intelligence,
)

OIAR_010_BUILD_ID="OIAR-010"
OIAR_010_REVISION="OIAR_010_OPERATOR_TERMINAL_PERSISTED_INTELLIGENCE_BINDING_V1"

TOKENS=(
    "best markets oracle understands right now",
    "best markets oracle understands",
    "rank trader intelligence",
    "historically proven live opportunities",
    "learned markets that are currently useful",
    "markets oracle knows best right now",
    "rank live opportunities",
    "what should i watch right now",
)

def is_persisted_trader_intelligence_query(query):
    normalized=" ".join(str(query).lower().split())
    return any(token in normalized for token in TOKENS)

def bind_persisted_trader_intelligence(base_module,root=None):
    if getattr(base_module,"_oiar010_bound",False):
        return base_module

    original=base_module.display_query
    active_root=Path(root or base_module.repository_root()).resolve()

    def display_query(query,*,session=None,root=None,builder=None,write=print):
        canonical=base_module.normalize_query(query)
        use_root=Path(root or active_root).resolve()

        if is_persisted_trader_intelligence_query(canonical):
            result=read_fast_trader_intelligence(use_root,10)
            for line in result.lines:
                write(line)

            if session is not None:
                session.query_count+=1
                session.last_query=canonical
                session.last_session_id="OIAR-010:"+result.snapshot_id[:16]
                session.active_panel_index=0

            return result

        kwargs={"session":session,"root":use_root,"write":write}
        if builder is not None:
            kwargs["builder"]=builder
        return original(canonical,**kwargs)

    base_module.display_query=display_query
    base_module._oiar010_bound=True
    return base_module
