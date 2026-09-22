from dataclasses import dataclass
OIAR_011_BUILD_ID="OIAR-011"
@dataclass(frozen=True)
class TraderMarketIdentity:
 market_id:str;display_name:str;category:str;identity_quality:str;read_only:bool=True;execution_authority:bool=False
def translate_market_identity(x):
 x=str(x).strip().upper()
 if not x: raise ValueError("market_id required")
 rules=(("KXBTC","Bitcoin","crypto"),("KXETH","Ethereum","crypto"),("KXXRP","XRP","crypto"),("KXSOL","Solana","crypto"),("KXMLB","MLB","sports"),("KXNFL","NFL","sports"),("KXWNBA","WNBA","sports"),("KXNBA","NBA","sports"),("KXATP","ATP tennis","sports"),("KXWTA","WTA tennis","sports"),("KXMLS","MLS","sports"),("KXLIGA","Liga MX","sports"))
 for p,n,c in rules:
  if x.startswith(p): return TraderMarketIdentity(x,n+" market",c,"STRUCTURED")
 if x.startswith("KXMVECROSSCATEGORY"): return TraderMarketIdentity(x,"Cross-category combination market","multi-market","FAMILY_ONLY")
 if x.startswith("KXMVESPORTS"): return TraderMarketIdentity(x,"Multi-game sports combination market","sports","FAMILY_ONLY")
 return TraderMarketIdentity(x,x.split("-")[0]+" market","unknown","FAMILY_ONLY")
