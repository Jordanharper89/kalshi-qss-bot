from __future__ import annotations
from dataclasses import dataclass

READ_ONLY=True
EXECUTION_AUTHORITY=False
PROBABILITY_ENABLED=False

@dataclass(frozen=True,slots=True)
class SourceRequirement:
    topic:str
    source_family:str
    authority_tier:str
    existing_adapter:bool
    rationale:str

REQUIREMENTS=(
 SourceRequirement("weather","NWS/NOAA","AUTHORITATIVE",True,"warnings forecasts storms climate"),
 SourceRequirement("macroeconomics","BLS","AUTHORITATIVE",False,"CPI employment payrolls"),
 SourceRequirement("macroeconomics","BEA","AUTHORITATIVE",False,"GDP income spending"),
 SourceRequirement("macroeconomics","Federal Reserve/FRED","AUTHORITATIVE",False,"rates monetary policy macro series"),
 SourceRequirement("politics_elections","Official election authorities","AUTHORITATIVE",False,"certified election results"),
 SourceRequirement("politics_elections","FEC","AUTHORITATIVE",False,"federal campaign and candidate records"),
 SourceRequirement("corporate_finance","SEC EDGAR","AUTHORITATIVE",False,"filings material disclosures"),
 SourceRequirement("energy_commodities","EIA","AUTHORITATIVE",False,"petroleum gas electricity"),
 SourceRequirement("energy_commodities","USDA","AUTHORITATIVE",False,"agriculture crop reports"),
 SourceRequirement("legal_regulatory","Federal Register","AUTHORITATIVE",True,"rules notices executive agency actions"),
 SourceRequirement("legal_regulatory","CourtListener/official courts","PRIMARY_OR_HIGH_RELIABILITY",False,"court opinions and dockets"),
 SourceRequirement("health","CDC","AUTHORITATIVE",False,"public health surveillance"),
 SourceRequirement("health","FDA","AUTHORITATIVE",False,"drug/device regulatory actions"),
 SourceRequirement("transport","FAA","AUTHORITATIVE",False,"aviation restrictions and operations"),
 SourceRequirement("transport","TSA","AUTHORITATIVE",False,"checkpoint/travel statistics"),
 SourceRequirement("transport","Maritime/port authorities","AUTHORITATIVE",False,"shipping and port state"),
 SourceRequirement("science_space","NASA","AUTHORITATIVE",False,"missions launches space events"),
 SourceRequirement("geopolitics","State/Defense/UN official releases","AUTHORITATIVE",False,"official geopolitical state"),
 SourceRequirement("sports","Official league/team feeds","PRIMARY",False,"schedules results injuries where available"),
 SourceRequirement("crypto","Coinbase/chain RPC/indexers","PRIMARY",False,"spot/chain state independent of Kalshi"),
 SourceRequirement("other","Unmapped","NONE",False,"requires topic discovery before adapter assignment"),
 SourceRequirement("geological","USGS","AUTHORITATIVE",True,"earthquakes geological events"),
)

def requirements_for_topic(topic):
    return tuple(x for x in REQUIREMENTS if x.topic==str(topic))
