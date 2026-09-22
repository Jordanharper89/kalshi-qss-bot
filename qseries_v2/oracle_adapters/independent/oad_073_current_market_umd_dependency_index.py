from __future__ import annotations
from types import MappingProxyType
from qseries_v2.universal_market_discovery.umd_109_market_semantic_profile import semantic_key
from qseries_v2.oracle_adapters.independent.oad_069_current_open_kalshi_market_index import fetch_current_open_kalshi_market_index
from qseries_v2.oracle_adapters.independent.oad_071_semantic_noise_rejection import strong_phrases
READ_ONLY=True;EXECUTION_AUTHORITY=False;PROBABILITY_ENABLED=False
def market_dependency_facts(m):
    text=" ".join(str(m.get(k,"") or "") for k in ("ticker","event_ticker","title","subtitle","yes_sub_title","no_sub_title","rules_primary"))
    phrases=strong_phrases(text)
    facts=set()
    for x in phrases:
        if any(k in x for k in ("earthquake","hurricane","tornado","flood","storm","snow","rain","temperature","heat","wind")): facts.add(("event",x))
        if any(k in x for k in ("bitcoin","ethereum","solana","btc","eth")): facts.add(("asset",x))
        if any(k in x for k in ("cpi","inflation","unemployment","payroll","gdp","interest-rate","fed-rate")): facts.add(("metric",x))
        if any(k in x for k in ("election","president","senate","governor","primary")): facts.add(("event",x))
        if any(k in x for k in ("texas","california","florida","new-york","washington","alaska","hawaii","gulf","atlantic","pacific")): facts.add(("geography",x))
    return tuple(sorted(facts))
def build_current_market_dependency_index(limit=1000):
    markets,_=fetch_current_open_kalshi_market_index(limit=limit)
    index={}
    fact_counts=0
    for m in markets:
        ticker=str(m.get("ticker","")).strip()
        if not ticker: continue
        facts=market_dependency_facts(m);fact_counts+=len(facts)
        for kind,key in facts:index.setdefault(kind+"="+semantic_key(key),[]).append(ticker)
    frozen=MappingProxyType({k:tuple(sorted(set(v))) for k,v in sorted(index.items())})
    return markets,frozen,fact_counts
