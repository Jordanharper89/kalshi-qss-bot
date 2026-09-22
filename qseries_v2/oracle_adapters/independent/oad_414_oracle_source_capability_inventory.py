from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import ast,re
READ_ONLY=True; EXECUTION_AUTHORITY=False; PROBABILITY_ENABLED=False
@dataclass(frozen=True,slots=True)
class SourceCapability:
 module:str; source_family:str; capability:str; authority:str
PATTERNS=(("weather","NWS/NOAA","AUTHORITATIVE"),("usgs","USGS","AUTHORITATIVE"),("sports","SPORTS_OFFICIAL","PRIMARY"),("mlb","MLB_OFFICIAL","PRIMARY"),("nhl","NHL_OFFICIAL","PRIMARY"),("economic","ECONOMIC_OFFICIAL","AUTHORITATIVE"),("bls","BLS","AUTHORITATIVE"),("cdc","CDC","AUTHORITATIVE"),("health","PUBLIC_HEALTH_OFFICIAL","AUTHORITATIVE"),("coinbase","COINBASE","PRIMARY"),("bitcoin","BITCOIN_CHAIN","PRIMARY"),("ethereum","ETHEREUM_CHAIN","PRIMARY"),("solana","SOLANA_CHAIN","PRIMARY"),("federal_register","FEDERAL_REGISTER","AUTHORITATIVE"),("gmgn","GMGN","SUPPLEMENTARY"))
def _cap(name):
 for x in ('persistence','readback','acquisition','adapter','foundation','runtime','source','intelligence','gate'):
  if x in name:return x.upper()
 return 'OTHER'
def inventory_source_capabilities(root='.'):
 base=Path(root)/'qseries_v2/oracle_adapters/independent'; out=[]
 for p in sorted(base.glob('oad_*.py')):
  n=p.stem.lower()
  for token,fam,auth in PATTERNS:
   if token in n:
    out.append(SourceCapability(p.stem,fam,_cap(n),auth)); break
 return tuple(out)
def source_family_counts(root='.'):
 from collections import Counter
 return dict(Counter(x.source_family for x in inventory_source_capabilities(root)))
