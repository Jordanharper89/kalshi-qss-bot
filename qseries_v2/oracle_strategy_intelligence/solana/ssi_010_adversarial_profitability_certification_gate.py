def certify(reports):
 e=[r for r in reports if r.get("n",0)>0];n=sum(r["n"] for r in e);p=sum(r.get("expectancy",0)>0 for r in e);w=sum(r.get("expectancy",0)*r["n"] for r in e)/n if n else 0.0
 state="GENERALIZATION_NOT_CERTIFIED"
 if len(e)>=3 and n>=15 and p>=max(2,(len(e)+1)//2) and w>0:state="MULTI_TOKEN_POSITIVE_NET_EXPECTANCY_FOUND"
 return {"eligible_tokens":len(e),"positive_tokens":p,"examples":n,"weighted_net_expectancy":w,"state":state,"read_only":True,"execution_authority":False}
