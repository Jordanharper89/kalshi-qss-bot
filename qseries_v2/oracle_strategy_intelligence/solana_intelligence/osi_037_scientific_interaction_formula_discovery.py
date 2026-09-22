from __future__ import annotations
import itertools,math

def _truth(v):
 if isinstance(v,bool):return v
 if isinstance(v,(int,float)):return v>0
 if isinstance(v,str):return v.lower() in ("true","yes","positive","buy","bull","rising","increasing")
 return False

def discover(matrix:dict,horizon:str,min_sample:int=5,max_order:int=3)->dict:
 cases=matrix.get("comparable_cases",[]);features=matrix.get("feature_names",[])
 rows=[]
 for order in range(1,min(max_order,len(features))+1):
  for combo in itertools.combinations(features,order):
   matched=[c for c in cases if all(_truth(c.get("features",{}).get(f)) for f in combo)]
   vals=[]
   for c in matched:
    o=c.get("outcomes",{}).get(str(horizon))
    if isinstance(o,(int,float)):vals.append(float(o))
   if len(vals)<min_sample:continue
   avg=sum(vals)/len(vals);wins=sum(1 for x in vals if x>0);losses=sum(1 for x in vals if x<=0)
   rows.append({"formula":" + ".join(combo),"order":order,"sample_size":len(vals),"mean_return":avg,
                "positive_frequency":wins/len(vals),"wins":wins,"losses":losses})
 rows.sort(key=lambda x:(x["mean_return"],x["sample_size"]),reverse=True)
 return {"revision":"OSI_037","horizon":str(horizon),"candidates":rows,
         "candidate_count":len(rows),"raw_frequency_is_calibrated_probability":False,
         "execution_authority":False,"read_only":True}
