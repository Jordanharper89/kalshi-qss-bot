from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
import json
from types import MappingProxyType
OCL_013_BUILD_ID="OCL-013";OCL_013_REVISION="OCL_013_CROSS_MARKET_DEPENDENCY_LEARNING_V1"
def _h(v):return sha256(json.dumps(v,sort_keys=True,separators=(",",":"),default=str).encode()).hexdigest()
@dataclass(frozen=True)
class CrossMarketDependency:
 source_market_id:str; target_market_id:str; paired_count:int; concordant_count:int; discordant_count:int; dependency_score:float; dependency_hash:str
def learn_cross_market_dependency(source_market_id,target_market_id,pairs):
 if source_market_id==target_market_id:raise ValueError("cross-market identity required")
 rows=tuple((bool(a),bool(b)) for a,b in pairs)
 if not rows:raise ValueError("paired evidence required")
 con=sum(1 for a,b in rows if a==b);dis=len(rows)-con;score=(con-dis)/len(rows)
 raw={"source_market_id":source_market_id,"target_market_id":target_market_id,"paired_count":len(rows),"concordant_count":con,"discordant_count":dis,"dependency_score":score}
 return CrossMarketDependency(source_market_id,target_market_id,len(rows),con,dis,score,_h(raw))
def verify_cross_market_dependency(d):
 raw={"source_market_id":d.source_market_id,"target_market_id":d.target_market_id,"paired_count":d.paired_count,"concordant_count":d.concordant_count,"discordant_count":d.discordant_count,"dependency_score":d.dependency_score}
 return d.source_market_id!=d.target_market_id and -1<=d.dependency_score<=1 and d.dependency_hash==_h(raw)
def build_ocl_013_certification_manifest():return MappingProxyType({"build_id":OCL_013_BUILD_ID,"revision":OCL_013_REVISION,"relationship":"observed_dependency_not_causation","execution":False})
def verify_ocl_013_cross_market_dependency_learning():
 d=learn_cross_market_dependency("a","b",((1,1),(1,1),(0,1)));return verify_cross_market_dependency(d)
