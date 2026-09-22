from __future__ import annotations
from dataclasses import dataclass, is_dataclass, asdict
from .oad_378_solana_oad317_exact_case_execution import invoke_oad317_exact
READ_ONLY=True
EXECUTION_AUTHORITY=False
@dataclass(frozen=True, slots=True)
class OAD317ResultContract:
    result_type:str; state:str; fields:tuple; downstream_hints:tuple; execution_authority:bool=False
def inspect_oad317_result(records):
    meta,result=invoke_oad317_exact(records); vals={}
    if isinstance(result,dict): vals=result
    elif is_dataclass(result):
        try: vals=asdict(result)
        except Exception: vals={}
    elif hasattr(result,"__dict__"): vals={k:v for k,v in vars(result).items() if not k.startswith("_")}
    hints=[]
    for k,v in vals.items():
        if any(x in str(k).lower() for x in ("ocl","learn","handoff","case","record","experience","state","payload")):
            hints.append((str(k),type(v).__name__))
    return OAD317ResultContract(meta.result_type,meta.result_state,meta.result_fields,tuple(hints),False),result
