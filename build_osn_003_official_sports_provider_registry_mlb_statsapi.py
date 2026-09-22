
from pathlib import Path

REVISION = 'OSN_003_OFFICIAL_SPORTS_PROVIDER_REGISTRY_MLB_STATSAPI_V1'
ROOT = Path.cwd()

def write(path: Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n", encoding="utf-8")
    print("[WRITE]", path.relative_to(ROOT))

def main():
    print("=" * 112)
    print(' OSN-003 OFFICIAL SPORTS PROVIDER REGISTRY + MLB STATSAPI PROVIDER INSTALLER')
    print("=" * 112)
    print("[ROOT]", ROOT)
    p = ROOT / 'qseries_v2/oracle_source_network/canonical/sports_event.py'
    if not p.exists():
        raise SystemExit("[FAIL] missing dependency: " + str(p))
    print("[PASS] dependency verified:", p.relative_to(ROOT))
    write(ROOT / 'qseries_v2/oracle_source_network/providers/registry.py', 'from dataclasses import dataclass\nfrom typing import Dict, Iterable\n\n@dataclass(frozen=True)\nclass ProviderSpec:\n    provider_id: str\n    sports: tuple\n    authority: str\n    base_url: str\n    read_only: bool = True\n    execution_authority: bool = False\n\n_REGISTRY: Dict[str, ProviderSpec] = {}\n\ndef register(spec: ProviderSpec) -> None:\n    if not spec.read_only or spec.execution_authority:\n        raise ValueError("OSN providers must be read-only and non-executing")\n    if spec.provider_id in _REGISTRY and _REGISTRY[spec.provider_id] != spec:\n        raise ValueError("provider id collision")\n    _REGISTRY[spec.provider_id] = spec\n\ndef get(provider_id: str) -> ProviderSpec:\n    return _REGISTRY[provider_id]\n\ndef all_providers() -> Iterable[ProviderSpec]:\n    return tuple(_REGISTRY.values())')
    write(ROOT / 'qseries_v2/oracle_source_network/providers/mlb_statsapi.py', 'from urllib.parse import urlencode\nfrom .registry import ProviderSpec, register\n\nPROVIDER_ID = "mlb_statsapi"\nBASE_URL = "https://statsapi.mlb.com/api/v1"\nSPEC = ProviderSpec(\n    provider_id=PROVIDER_ID,\n    sports=("baseball",),\n    authority="official_league",\n    base_url=BASE_URL,\n    read_only=True,\n    execution_authority=False,\n)\nregister(SPEC)\n\ndef schedule_url(date: str, hydrate: str = "") -> str:\n    params = {"sportId":"1","date":date}\n    if hydrate:\n        params["hydrate"] = hydrate\n    return f"{BASE_URL}/schedule?{urlencode(params)}"')
    write(ROOT / 'test_osn_003_official_sports_provider_registry_mlb_statsapi.py', 'import qseries_v2.oracle_source_network.providers.mlb_statsapi as mlb\nfrom qseries_v2.oracle_source_network.providers.registry import get\n\nspec = get("mlb_statsapi")\nassert spec.authority == "official_league"\nassert spec.read_only is True\nassert spec.execution_authority is False\nassert spec.base_url.startswith("https://statsapi.mlb.com/")\nu = mlb.schedule_url("2026-09-05")\nassert "sportId=1" in u and "date=2026-09-05" in u\nprint("[PASS] OSN-003 official provider registry + MLB provider certified")')
    print('[PASS] OSN-003 installed')

if __name__ == '__main__':
    main()
