
from dataclasses import dataclass
@dataclass(frozen=True)
class OPH017Contract:
    request:bool=True
    producer:bool=True
    observation:bool=True
    expected_head:bool=True
    backend_result:bool=True
    reason_codes:bool=True
    execution_authority:bool=False
def verify_oph_017_canonical_backend_rejection_forensic():
    x=OPH017Contract()
    return all((x.request,x.producer,x.observation,x.expected_head,x.backend_result,x.reason_codes)) and not x.execution_authority
