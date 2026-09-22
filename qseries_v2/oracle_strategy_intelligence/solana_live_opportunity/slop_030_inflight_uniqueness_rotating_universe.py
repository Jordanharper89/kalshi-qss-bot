from dataclasses import dataclass
from .slop_024_unresolved_prediction_surveillance import unresolved_view
READ_ONLY=True;EXECUTION_AUTHORITY=False
@dataclass(frozen=True,slots=True)
class AdmissionUniverse:
 candidates:tuple;blocked_tokens:tuple;execution_authority:bool=False
def admission_universe(discovered_tokens,root=None,limit=5):
 u=unresolved_view(root);blocked=set(u.tokens)
 fresh=tuple(x for x in dict.fromkeys(map(str,discovered_tokens)) if x not in blocked)
 return AdmissionUniverse(fresh[:int(limit)],tuple(sorted(blocked)),False)
def rotate(tokens,round_number):
 xs=tuple(tokens)
 if not xs:return ()
 n=int(round_number)%len(xs)
 return xs[n:]+xs[:n]
