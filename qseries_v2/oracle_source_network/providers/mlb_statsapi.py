from urllib.parse import urlencode
from .registry import ProviderSpec, register

PROVIDER_ID = "mlb_statsapi"
BASE_URL = "https://statsapi.mlb.com/api/v1"
SPEC = ProviderSpec(
    provider_id=PROVIDER_ID,
    sports=("baseball",),
    authority="official_league",
    base_url=BASE_URL,
    read_only=True,
    execution_authority=False,
)
register(SPEC)

def schedule_url(date: str, hydrate: str = "") -> str:
    params = {"sportId":"1","date":date}
    if hydrate:
        params["hydrate"] = hydrate
    return f"{BASE_URL}/schedule?{urlencode(params)}"
