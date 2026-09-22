from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime,timezone
from hashlib import sha256
import json
from .oad_227_crypto_learned_case_asof_snapshot_boundary import capture_crypto_learned_case_snapshot

READ_ONLY=True;PROBABILITY_ENABLED=False;DIRECTION_ENABLED=False;PUBLICATION_ALLOWED=False;EXECUTION_AUTHORITY=False

def _h(v):return sha256(json.dumps(v,sort_keys=True,separators=(",",":"),default=str).encode()).hexdigest()

@dataclass(frozen=True,slots=True)
class ProspectiveCryptoForecast:
    forecast_id:str
    asset:str
    created_at:str
    training_as_of_sequence:int
    training_snapshot_hash:str
    sample_size:int
    positive_count:int
    negative_or_flat_count:int
    internal_forecast_probability:float
    source_claims:tuple
    horizon_seconds:int=60
    probability_enabled:bool=False
    direction_enabled:bool=False
    publication_allowed:bool=False
    execution_authority:bool=False

def build_prospective_crypto_forecasts(root=None,per_asset_limit=512,created_at=None):
    snap=capture_crypto_learned_case_snapshot(root,per_asset_limit)
    now=created_at or datetime.now(timezone.utc).isoformat()
    by_asset={}
    for row in snap.rows:
        p=row[4] if isinstance(row[4],dict) else dict(row[4] or ())
        asset=str(p.get("asset") or "").upper()
        if asset and p.get("return_fraction") is not None:by_asset.setdefault(asset,[]).append(p)
    out=[]
    for asset,rows in sorted(by_asset.items()):
        pos=sum(float(p["return_fraction"])>0 for p in rows);n=len(rows)
        probability=(pos+1)/(n+2)  # auditable Beta(1,1) empirical forecast
        families={}
        for p in rows:
            y=float(p["return_fraction"])>0
            seen=set()
            for x in tuple(p.get("condition_vector") or ()):
                if isinstance(x,(list,tuple)) and x:
                    fam=str(x[0]).strip().lower()
                    if fam and fam not in seen:
                        families.setdefault(fam,[0,0]);families[fam][0]+=1;families[fam][1]+=int(y);seen.add(fam)
        claims=tuple((fam,cnt,(pc+1)/(cnt+2),((pc+1)/(cnt+2))>=.5) for fam,(cnt,pc) in sorted(families.items()))
        raw={"asset":asset,"created_at":now,"as_of":snap.as_of_sequence,"snapshot":snap.snapshot_hash,"n":n,"p":probability,"claims":claims}
        out.append(ProspectiveCryptoForecast(_h(raw),asset,now,snap.as_of_sequence,snap.snapshot_hash,n,pos,n-pos,probability,claims))
    return tuple(out)
