from dataclasses import dataclass
from threading import Lock

@dataclass(frozen=True)
class CanonicalWriteEnvelope:
    writer_id:str; priority:int; observations:tuple; admitted_sequence:int; execution_authority:bool=False

@dataclass(frozen=True)
class CanonicalWriterServiceState:
    accepted_batches:int; accepted_observations:int; completed_batches:int; completed_observations:int; rejected_batches:int; next_sequence:int; execution_authority:bool=False

class SingleCanonicalWriterService:
    def __init__(self):
        self._lock=Lock(); self._queue=[]; self._sequence=0
        self._accepted_batches=0; self._accepted_observations=0
        self._completed_batches=0; self._completed_observations=0; self._rejected_batches=0
    def submit(self,writer_id,observations,priority):
        items=tuple(observations)
        if not items:
            self._rejected_batches+=1; raise ValueError("empty canonical write batch")
        with self._lock:
            self._sequence+=1
            env=CanonicalWriteEnvelope(str(writer_id),int(priority),items,self._sequence,False)
            self._queue.append(env)
            self._accepted_batches+=1; self._accepted_observations+=len(items)
            return env
    def dequeue(self):
        with self._lock:
            if not self._queue: return None
            self._queue.sort(key=lambda x:(-x.priority,x.admitted_sequence))
            return self._queue.pop(0)
    def mark_completed(self,envelope):
        self._completed_batches+=1; self._completed_observations+=len(envelope.observations)
    def state(self):
        return CanonicalWriterServiceState(self._accepted_batches,self._accepted_observations,self._completed_batches,self._completed_observations,self._rejected_batches,self._sequence+1,False)

def verify_oph_001_single_canonical_writer_service():
    s=SingleCanonicalWriterService()
    s.submit("coverage",("c1","c2"),20); s.submit("fast_lane",("f1",),100)
    a=s.dequeue(); b=s.dequeue(); s.mark_completed(a); s.mark_completed(b); st=s.state()
    return a.writer_id=="fast_lane" and b.writer_id=="coverage" and st.completed_observations==3 and not st.execution_authority
