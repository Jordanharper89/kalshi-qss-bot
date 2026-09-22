from __future__ import annotations
from dataclasses import dataclass
from .oad_302_solana_security_evidence_boundary import acquire_current_solana_security_evidence
READ_ONLY=True; PROBABILITY_ENABLED=False; DIRECTION_ENABLED=False; PUBLICATION_ALLOWED=False; EXECUTION_AUTHORITY=False
KEYS=("creator","creator_address","deployer","deployer_address","owner","owner_address","dev","dev_address")
@dataclass(frozen=True,slots=True)
class CreatorDeployerClaim:
    token_address:str; field_path:str; value:str; provider:str="gmgn"; oracle_verified:bool=False; execution_authority:bool=False
@dataclass(frozen=True,slots=True)
class CreatorDeployerReport:
    token_address:str; claims:tuple; claim_count:int; provider_claim_only:bool=True; execution_authority:bool=False
def _extract(token,v,path="",out=None):
    out=[] if out is None else out
    if isinstance(v,dict):
        for k,z in v.items():
            p=(path+"."+str(k)).strip(".")
            if str(k).lower() in KEYS and z not in (None,"",[],{}): out.append(CreatorDeployerClaim(token,p,str(z),"gmgn",False,False))
            if isinstance(z,(dict,list)): _extract(token,z,p,out)
    elif isinstance(v,list):
        for i,z in enumerate(v):
            if isinstance(z,(dict,list)): _extract(token,z,path+"["+str(i)+"]",out)
    return out
def acquire_current_creator_deployer_claims(timeout_seconds=30.0):
    x=acquire_current_solana_security_evidence(timeout_seconds); rows=tuple(_extract(x.token_address,x.gmgn_security))
    return CreatorDeployerReport(x.token_address,rows,len(rows),True,False)
