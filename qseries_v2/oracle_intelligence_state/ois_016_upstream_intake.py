from dataclasses import dataclass
@dataclass(frozen=True)
class UpstreamIntake: source:str; subject_id:str; sequence:int; state_hash:str; received_ns:int
def build_upstream_intake(source,subject_id,sequence,state_hash,received_ns):
 if not source or not subject_id or sequence<0 or received_ns<0 or len(state_hash)!=64:raise ValueError("valid intake required")
 return UpstreamIntake(source,subject_id,sequence,state_hash,received_ns)
def order_upstream_intake(xs):
 r=tuple(sorted(xs,key=lambda x:(x.source,x.subject_id,x.sequence,x.received_ns)))
 if len({(x.source,x.subject_id,x.sequence) for x in r})!=len(r):raise ValueError("duplicate sequence")
 return r
def verify_ois_016_continuous_upstream_intelligence_intake():
 a=build_upstream_intake("osr","btc",2,"a"*64,2);b=build_upstream_intake("osr","btc",1,"b"*64,1)
 return [x.sequence for x in order_upstream_intake((a,b))]==[1,2]
