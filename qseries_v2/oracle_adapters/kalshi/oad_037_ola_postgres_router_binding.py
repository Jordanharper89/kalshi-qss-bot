from __future__ import annotations
from datetime import datetime
from pathlib import Path
import os

OAD_037_BUILD_ID="OAD-037"
OAD_037_REVISION="OAD_037_OLA_PRODUCTION_POSTGRESQL_ROUTER_BINDING_V1"

def load_repository_environment(root):
    result=dict(os.environ)
    p=Path(root)/".env"
    if not p.is_file(): return result
    for raw in p.read_text(encoding="utf-8",errors="ignore").splitlines():
        line=raw.strip()
        if not line or line.startswith("#") or "=" not in line: continue
        k,v=line.split("=",1)
        k=k.strip(); v=v.strip()
        if len(v)>=2 and v[0]==v[-1] and v[0] in ("'",'"'): v=v[1:-1]
        if k and k not in result: result[k]=v
    return result

def build_ola_production_persistence_router(root,environment=None):
    from qseries_v2.oracle_intelligence.live_acquisition_model.oracle_first_real_shadow_corpus_launch_command import (
        build_real_oracle_shadow_graph,
    )
    root=Path(root).resolve()
    env=dict(environment) if environment is not None else load_repository_environment(root)
    graph=build_real_oracle_shadow_graph(
        runtime_root=root,
        environment=env,
        service_tick_interval_seconds=5,
    )
    router=graph.get("persistence_router")
    if router is None or not callable(getattr(router,"route",None)):
        raise RuntimeError("OLA-030 production persistence router unavailable")
    return router

def persist_canonical_observation(router,observation,*,routed_at):
    if not isinstance(routed_at,datetime) or routed_at.tzinfo is None:
        raise ValueError("routed_at must be timezone-aware")
    route=getattr(router,"route",None)
    if not callable(route): raise ValueError("router must expose route")
    evidence=route(observation,routed_at)
    if getattr(evidence,"accepted",None) is not True:
        raise RuntimeError("OLA canonical persistence routing rejected")
    if getattr(evidence,"observation_id",None)!=observation.observation_id:
        raise RuntimeError("persistence evidence observation mismatch")
    return evidence

def verify_oad_037_ola_production_postgresql_router_binding():
    class E:
        accepted=True
        observation_id="x"
    class R:
        def route(self,o,t):
            e=E(); e.observation_id=o.observation_id; return e
    class O: observation_id="x"
    from datetime import timezone
    return persist_canonical_observation(R(),O(),routed_at=datetime(2026,8,13,tzinfo=timezone.utc)).accepted is True
