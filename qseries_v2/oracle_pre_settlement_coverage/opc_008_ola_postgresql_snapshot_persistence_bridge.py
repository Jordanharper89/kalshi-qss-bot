from dataclasses import dataclass
from pathlib import Path
import os
from qseries_v2.oracle_intelligence.live_acquisition.oracle_postgresql_canonical_observation_persistence_backend import OraclePostgreSQLCanonicalObservationPersistenceBackend
from qseries_v2.oracle_intelligence.live_acquisition.oracle_postgresql_canonical_observation_persistence_router import OraclePostgreSQLCanonicalObservationPersistenceRouter

@dataclass(frozen=True)
class SnapshotPersistenceSummary:
    requested:int
    accepted:int
    rejected:int
    read_only_intelligence:bool=True
    execution_authority:bool=False

def _db(root):
    u=os.environ.get("DATABASE_URL") or os.environ.get("ORACLE_DATABASE_URL")
    if u:return u
    p=Path(root)/".env"
    if p.is_file():
        for line in p.read_text(encoding="utf-8",errors="ignore").splitlines():
            if "=" in line and not line.lstrip().startswith("#"):
                k,v=line.split("=",1)
                if k.strip() in ("DATABASE_URL","ORACLE_DATABASE_URL"): return v.strip().strip('"').strip("'")
    raise RuntimeError("DATABASE_URL / ORACLE_DATABASE_URL not configured")

def build_opc_postgresql_router(root=None):
    root=Path(root or Path.cwd()).resolve(); url=_db(root)
    import psycopg
    backend=OraclePostgreSQLCanonicalObservationPersistenceBackend(
        connection_factory=lambda: psycopg.connect(url),auto_initialize_schema=False)
    return OraclePostgreSQLCanonicalObservationPersistenceRouter(
        persistence_backend=backend,
        route_id="oracle.postgresql.kalshi.opc.snapshot.router.v1",
        routing_metadata={"production_path":True,"shadow_mode":True,"opc_build":"OPC-008"},
        replay_metadata={"replay_source":"OPC-008"},
        audit_metadata={"component":"oracle_pre_settlement_coverage"})

def persist_snapshot_batch(observations,*,routed_at,router):
    obs=tuple(observations)
    if not obs:return SnapshotPersistenceSummary(0,0,0,True,False)
    ev=tuple(router.route_batch(obs,routed_at))
    accepted=sum(1 for x in ev if getattr(x,"accepted",False) is True)
    return SnapshotPersistenceSummary(len(obs),accepted,len(obs)-accepted,True,False)

def verify_opc_008_ola_postgresql_snapshot_persistence_bridge():
    class E: accepted=True
    class R:
        def route_batch(self,observations,routed_at): return tuple(E() for _ in observations)
    x=persist_snapshot_batch((1,2),routed_at=None,router=R())
    return x.requested==2 and x.accepted==2 and x.rejected==0 and not x.execution_authority
