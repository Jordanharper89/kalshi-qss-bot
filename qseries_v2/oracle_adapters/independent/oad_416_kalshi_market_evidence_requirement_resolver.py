from __future__ import annotations
from dataclasses import dataclass
from qseries_v2.oracle_adapters.independent.oad_076_precision_current_market_topic_classifier import classify_market_topic
from qseries_v2.oracle_adapters.independent.oad_105_authoritative_source_requirement_router import assign_source_requirement
READ_ONLY=True; EXECUTION_AUTHORITY=False; PROBABILITY_ENABLED=False
@dataclass(frozen=True,slots=True)
class MarketEvidenceRequirement:
 ticker:str; domain:str; source_families:tuple[str,...]; state:str
EXTRA={'weather':('NWS/NOAA',),'crypto':('COINBASE','BITCOIN_CHAIN','ETHEREUM_CHAIN','SOLANA_CHAIN'),'macroeconomics':('BLS','ECONOMIC_OFFICIAL'),'health':('CDC','PUBLIC_HEALTH_OFFICIAL'),'sports':('SPORTS_OFFICIAL',),'energy_commodities':('EIA',),'corporate_finance':('SEC_EDGAR',),'politics_elections':('ELECTION_OFFICIAL',),'science_space':('NASA',),'transport':('FAA',)}
def resolve_market_evidence_requirement(market):
 c=classify_market_topic(market); r=assign_source_requirement(c.primary_topic)
 fam=EXTRA.get(c.primary_topic,tuple(r.authoritative_source_families))
 state='RESOLVED' if fam and c.primary_topic!='other' else 'UNMAPPED'
 return MarketEvidenceRequirement(str(market.get('ticker','')),c.primary_topic,tuple(fam),state)
def resolve_market_cohort(markets):return tuple(resolve_market_evidence_requirement(x) for x in markets)
