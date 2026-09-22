from __future__ import annotations
from pathlib import Path
from .oracle_historical_experience_terminal_surface import is_historical_experience_query,answer_historical_experience_query
OHE_005_BUILD_ID="OHE-005";OHE_005_REVISION="OHE_005_OPERATOR_TERMINAL_HISTORICAL_EXPERIENCE_BINDING_V1"
def bind_historical_experience_surface(base_module,root=None):
    if getattr(base_module,"_ohe005_bound",False):return base_module
    original=base_module.display_query;active_root=Path(root or base_module.repository_root()).resolve()
    def display_query(query,*,session=None,root=None,builder=None,write=print):
        canonical=base_module.normalize_query(query);use_root=Path(root or active_root).resolve()
        if is_historical_experience_query(canonical):
            result=answer_historical_experience_query(use_root,canonical)
            for line in result.lines:write(line)
            if session is not None:
                session.query_count+=1;session.last_query=canonical;session.last_session_id="OHE-005:"+result.learner_state_hash[:16];session.active_panel_index=0
            return result
        kwargs={"session":session,"root":use_root,"write":write}
        if builder is not None:kwargs["builder"]=builder
        return original(canonical,**kwargs)
    base_module.display_query=display_query;base_module._ohe005_bound=True;base_module.OHE_005_BOUND=True
    return base_module
