from dataclasses import dataclass
@dataclass(frozen=True)
class AdapterCoverageState:
 adapter_id:str; eligible_markets:int; subscribed_markets:int; coverage_ratio:float; complete:bool
def build_adapter_coverage_state(adapter_id,eligible_markets,subscribed_markets):
 e=int(eligible_markets); s=int(subscribed_markets)
 if not adapter_id or e<0 or s<0 or s>e: raise ValueError("valid coverage required")
 r=1.0 if e==0 else s/e
 return AdapterCoverageState(adapter_id,e,s,r,s==e)
def verify_ois_042_live_subscription_universe_coverage_state():
 return build_adapter_coverage_state("kalshi_universal",100,100).complete and not build_adapter_coverage_state("kalshi_universal",100,99).complete
