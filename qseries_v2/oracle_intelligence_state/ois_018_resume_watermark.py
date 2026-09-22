from dataclasses import dataclass
from .ois_017_intake_checkpoint import IntakeCheckpoint
@dataclass(frozen=True)
class ResumeWatermark: source:str; subject_id:str; last_sequence:int; checkpoint_hash:str
def build_resume_watermark(c):
 if not isinstance(c,IntakeCheckpoint):raise ValueError("checkpoint required")
 return ResumeWatermark(c.source,c.subject_id,c.sequence,c.checkpoint_hash)
def should_accept_after_resume(w,source,subject_id,sequence):
 if (w.source,w.subject_id)!=(source,subject_id):raise ValueError("stream mismatch")
 return sequence>w.last_sequence
def verify_ois_018_restart_safe_resume_watermark():
 from .ois_016_upstream_intake import build_upstream_intake
 from .ois_017_intake_checkpoint import build_intake_checkpoint
 w=build_resume_watermark(build_intake_checkpoint(build_upstream_intake("osr","btc",5,"a"*64,5)))
 return not should_accept_after_resume(w,"osr","btc",5) and should_accept_after_resume(w,"osr","btc",6)
