from __future__ import annotations
from dataclasses import dataclass
from qseries_v2.oracle_adapters.independent.oad_083_deep_unresolved_market_classification import deep_classify_market
from qseries_v2.oracle_adapters.independent.oad_086_structural_sports_market_detector import detect_sports_market
READ_ONLY=True;EXECUTION_AUTHORITY=False;PROBABILITY_ENABLED=False
@dataclass(frozen=True,slots=True)
class ExpandedDomain:
 ticker:str;domain:str;evidence:tuple[str,...]
DOMAIN_TERMS={
 "macroeconomics":("inflation","cpi","gdp","unemployment","jobs","payroll","interest rate","federal reserve","fed funds","treasury yield"),
 "politics_elections":("election","president","senate","house of representatives","governor","approval rating","primary","electoral"),
 "corporate_finance":("earnings","revenue","eps","ipo","merger","acquisition","market cap","stock price","sec filing"),
 "crypto":("bitcoin","ethereum","solana","crypto","btc","eth"),
 "weather":("hurricane","tornado","rainfall","snowfall","temperature","flood","tropical storm"),
 "energy_commodities":("crude oil","natural gas","gasoline","gold","silver","wheat","corn","soybean"),
 "legal_regulatory":("supreme court","court ruling","lawsuit","indictment","regulation","tariff","sanction"),
 "health":("cdc","fda","vaccine","outbreak","disease","drug approval"),
 "transport":("faa","tsa","airport","flight","shipping","port","rail"),
 "science_space":("nasa","rocket","spacecraft","asteroid","moon","mars"),
 "geopolitics":("ceasefire","nato","invasion","military","peace deal","treaty"),
 "technology":("openai","artificial intelligence","ai model","iphone","android","semiconductor","chip"),
 "entertainment_awards":("oscar","grammy","emmy","box office","album","movie","billboard"),
}
def expanded_domain_classify(m):
 b=deep_classify_market(m)
 if b.topic!="other":return ExpandedDomain(b.ticker,b.topic,b.evidence)
 if detect_sports_market(m).is_sports:return ExpandedDomain(str(m.get("ticker","")),"sports",("structural_sports",))
 text=" ".join(str(m.get(k,"") or "") for k in ("ticker","event_ticker","series_ticker","title","subtitle","yes_sub_title","no_sub_title","rules_primary","rules_secondary")).lower()
 hits=[]
 for d,terms in DOMAIN_TERMS.items():
  found=tuple(x for x in terms if x in text)
  if found:hits.append((len(found),d,found))
 if not hits:return ExpandedDomain(str(m.get("ticker","")),"other",())
 hits.sort(key=lambda x:(-x[0],x[1]));_,d,found=hits[0]
 return ExpandedDomain(str(m.get("ticker","")),d,found)
