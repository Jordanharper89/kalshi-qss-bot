from dataclasses import dataclass
from .oph_001_single_canonical_writer_service import SingleCanonicalWriterService
from .oph_002_priority_observation_ingestion_queue import admit_observations

@dataclass(frozen=True)
class AdapterAdmissionReceipt:
    adapter_id:str; lane:str; priority:int; observation_count:int; writer_sequence:int; direct_postgresql_write_authority:bool=False; execution_authority:bool=False

class UniversalAdapterAdmissionGateway:
    def __init__(self,writer_service=None): self.writer_service=writer_service or SingleCanonicalWriterService()
    def submit(self,adapter_id,lane,observations):
        a=admit_observations(adapter_id,lane,observations)
        e=self.writer_service.submit(a.adapter_id,a.observations,a.priority)
        return AdapterAdmissionReceipt(a.adapter_id,a.lane,a.priority,len(a.observations),e.admitted_sequence,False,False)

def verify_oph_004_universal_adapter_admission_gateway():
    g=UniversalAdapterAdmissionGateway()
    xs=[g.submit("kalshi","FAST_LANE",("a",)),g.submit("coinbase","LIVE_ADAPTER",("b",)),g.submit("polymarket","NORMAL",("c",)),g.submit("solana","NORMAL",("d",))]
    return xs[0].priority>xs[1].priority>xs[2].priority and all(not x.direct_postgresql_write_authority and not x.execution_authority for x in xs)
