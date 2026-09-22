from dataclasses import dataclass
@dataclass(frozen=True)
class PrioritizedCoverageMarket:
    ticker:str; score:int; reason_codes:tuple; read_only:bool=True; execution_allowed:bool=False
def prioritize_coverage(items,facts=None):
    facts=facts or {}; out=[]
    for item in items:
        t=str(getattr(item,"ticker",item)); f=facts.get(t,{})
        s=100; r=["UNCOVERED"]
        if f.get("active"): s+=40; r.append("ACTIVE")
        if f.get("volume",0)>0: s+=20; r.append("HAS_VOLUME")
        if f.get("close_soon"): s+=30; r.append("CLOSE_SOON")
        out.append(PrioritizedCoverageMarket(t,s,tuple(r)))
    return tuple(sorted(out,key=lambda x:(-x.score,x.ticker)))
def verify_opc_012_coverage_priority_engine():
    x=prioritize_coverage(("A","B"),{"B":{"active":True}})
    return x[0].ticker=="B" and x[0].score>x[1].score
