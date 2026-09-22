from dataclasses import dataclass
READ_ONLY=True;EXECUTION_AUTHORITY=False
@dataclass(frozen=True,slots=True)
class RefreshPlan:
 round_number:int;refresh_discovery:bool;reason:str;execution_authority:bool=False
def plan_refresh(round_number,refresh_every_rounds=3):
 n=int(round_number);k=max(1,int(refresh_every_rounds));yes=n==1 or n%k==0
 return RefreshPlan(n,yes,"PERIODIC_LIVE_REFRESH" if yes else "CONTINUE_HOT_SURVEILLANCE",False)
