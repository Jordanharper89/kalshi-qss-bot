from dataclasses import dataclass
from .ois_004_query_snapshot import IntelligenceStateSnapshot,query_intelligence_state
@dataclass(frozen=True)
class ServedReadModel: snapshot_hash:str; generation:int; subject_count:int; read_only:bool=True
def build_served_read_model(s,generation):
 if not isinstance(s,IntelligenceStateSnapshot) or generation<1:raise ValueError("snapshot required")
 return ServedReadModel(s.snapshot_hash,generation,len(s.states),True)
def serve_subject(s,subject_id):return query_intelligence_state(s,subject_id)
def verify_ois_019_continuous_read_model_serving():
 from .ois_002_osr_intake_boundary import build_osr_state_intake
 from .ois_003_canonical_state import assemble_canonical_intelligence_state
 from .ois_004_query_snapshot import build_intelligence_state_snapshot
 x=assemble_canonical_intelligence_state(build_osr_state_intake("btc","supported",.8,.9,.1,False,"a"*64),"b"*64)
 s=build_intelligence_state_snapshot((x,))
 return build_served_read_model(s,1).read_only and serve_subject(s,"btc").subject_id=="btc"
