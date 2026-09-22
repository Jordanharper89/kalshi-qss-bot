
from pathlib import Path

REVISION = 'OSN_001_ORACLE_SOURCE_NETWORK_SUBSYSTEM_FOUNDATION_V1'
ROOT = Path.cwd()

def write(path: Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n", encoding="utf-8")
    print("[WRITE]", path.relative_to(ROOT))

def main():
    print("=" * 112)
    print(' OSN-001 ORACLE SOURCE NETWORK SUBSYSTEM FOUNDATION INSTALLER')
    print("=" * 112)
    print("[ROOT]", ROOT)
    matches = list(ROOT.glob('qseries_v2/oracle_adapters/independent/oad_414_*.py'))
    if not matches:
        raise SystemExit('[FAIL] missing dependency: OAD-414')
    print("[PASS] dependency verified:", matches[0].relative_to(ROOT))
    matches = list(ROOT.glob('qseries_v2/oracle_adapters/independent/oad_415_*.py'))
    if not matches:
        raise SystemExit('[FAIL] missing dependency: OAD-415')
    print("[PASS] dependency verified:", matches[0].relative_to(ROOT))
    matches = list(ROOT.glob('qseries_v2/oracle_adapters/independent/oad_416_*.py'))
    if not matches:
        raise SystemExit('[FAIL] missing dependency: OAD-416')
    print("[PASS] dependency verified:", matches[0].relative_to(ROOT))
    matches = list(ROOT.glob('qseries_v2/oracle_adapters/independent/oad_417_*.py'))
    if not matches:
        raise SystemExit('[FAIL] missing dependency: OAD-417')
    print("[PASS] dependency verified:", matches[0].relative_to(ROOT))
    matches = list(ROOT.glob('qseries_v2/oracle_adapters/independent/oad_418_*.py'))
    if not matches:
        raise SystemExit('[FAIL] missing dependency: OAD-418')
    print("[PASS] dependency verified:", matches[0].relative_to(ROOT))
    write(ROOT / 'qseries_v2/oracle_source_network/__init__.py', '"""Oracle Source Network (OSN)."""')
    write(ROOT / 'qseries_v2/oracle_source_network/contracts/__init__.py', '"""OSN contracts."""')
    write(ROOT / 'qseries_v2/oracle_source_network/providers/__init__.py', '"""OSN providers."""')
    write(ROOT / 'qseries_v2/oracle_source_network/canonical/__init__.py', '"""OSN canonical models."""')
    write(ROOT / 'qseries_v2/oracle_source_network/acquisition/__init__.py', '"""OSN acquisition."""')
    write(ROOT / 'qseries_v2/oracle_source_network/mapping/__init__.py', '"""OSN venue mapping."""')
    write(ROOT / 'qseries_v2/oracle_source_network/persistence/__init__.py', '"""OSN persistence boundary."""')
    write(ROOT / 'qseries_v2/oracle_source_network/health/__init__.py', '"""OSN health."""')
    write(ROOT / 'qseries_v2/oracle_source_network/certification/__init__.py', '"""OSN certification."""')
    write(ROOT / 'qseries_v2/oracle_source_network/foundation.py', 'from dataclasses import dataclass, asdict\nfrom typing import Tuple\nimport hashlib, json\n\nREVISION = "OSN_001_ORACLE_SOURCE_NETWORK_SUBSYSTEM_FOUNDATION_V1"\nEXECUTION_AUTHORITY = False\nVENUE_NEUTRAL = True\nUPSTREAM_CONTROL_PLANE = ("OAD-414","OAD-415","OAD-416","OAD-417","OAD-418")\n\n@dataclass(frozen=True)\nclass SourceNetworkDescriptor:\n    subsystem: str = "OSN"\n    purpose: str = "independent_source_network"\n    execution_authority: bool = False\n    venue_neutral: bool = True\n    upstream_control_plane: Tuple[str, ...] = UPSTREAM_CONTROL_PLANE\n\n    def fingerprint(self) -> str:\n        payload = json.dumps(asdict(self), sort_keys=True, separators=(",",":"))\n        return hashlib.sha256(payload.encode("utf-8")).hexdigest()\n\ndef descriptor() -> SourceNetworkDescriptor:\n    return SourceNetworkDescriptor()')
    write(ROOT / 'qseries_v2/oracle_source_network/contracts/source_contract.py', 'from dataclasses import dataclass\nfrom typing import Mapping, Any\n\n@dataclass(frozen=True)\nclass ProviderObservation:\n    provider: str\n    provider_event_id: str\n    observed_at: str\n    payload: Mapping[str, Any]\n    source_authority: str = "official"\n    execution_authority: bool = False')
    write(ROOT / 'test_osn_001_oracle_source_network_subsystem_foundation.py', 'from pathlib import Path\nfrom qseries_v2.oracle_source_network.foundation import descriptor, REVISION\n\nd = descriptor()\nassert REVISION == "OSN_001_ORACLE_SOURCE_NETWORK_SUBSYSTEM_FOUNDATION_V1"\nassert d.subsystem == "OSN"\nassert d.execution_authority is False\nassert d.venue_neutral is True\nassert d.upstream_control_plane == ("OAD-414","OAD-415","OAD-416","OAD-417","OAD-418")\nassert len(d.fingerprint()) == 64\n\nbase = Path("qseries_v2/oracle_source_network")\nfor name in ("contracts","providers","canonical","acquisition","mapping","persistence","health","certification"):\n    assert (base/name/"__init__.py").exists()\n\nprint("[PASS] OSN-001 subsystem foundation certified")')
    print('[PASS] OSN-001 installed')
    print('[PASS] execution_authority=FALSE')
    print('[PASS] venue_neutral=TRUE')

if __name__ == '__main__':
    main()
