from dataclasses import dataclass
from hashlib import sha256
from .ois_016_upstream_intake import UpstreamIntake
@dataclass(frozen=True)
class IntakeCheckpoint: source:str; subject_id:str; sequence:int; state_hash:str; checkpoint_hash:str
def build_intake_checkpoint(x,previous=None):
 if not isinstance(x,UpstreamIntake):raise ValueError("certified intake required")
 if previous and ((previous.source,previous.subject_id)!=(x.source,x.subject_id) or x.sequence<=previous.sequence):raise ValueError("checkpoint must advance")
 h=sha256(f"{x.source}|{x.subject_id}|{x.sequence}|{x.state_hash}".encode()).hexdigest()
 return IntakeCheckpoint(x.source,x.subject_id,x.sequence,x.state_hash,h)
def verify_ois_017_deterministic_intake_checkpointing():
 from .ois_016_upstream_intake import build_upstream_intake
 a=build_intake_checkpoint(build_upstream_intake("osr","btc",1,"a"*64,1))
 return build_intake_checkpoint(build_upstream_intake("osr","btc",2,"b"*64,2),a).sequence==2
