
from dataclasses import dataclass
from pathlib import Path
import json

ADMITTED=("NFL","NCAAF","NBA","NHL","MLS","EPL")

@dataclass(frozen=True)
class SportsSourceFoundationCertification:
    osn076_executable_source_foundation:bool
    osn077_uniform_canonical_provider:bool
    osn078_six_league_physical_gate:bool
    osn079_uniform_runtime_binding:bool
    admitted:tuple
    held:tuple
    blocked:tuple
    terminal_dependency:str
    source_foundation_ready:bool
    persistence_activation_next:bool
    continuous_worker_activation_next:bool
    execution_authority:bool=False

def certify(root=None):
    base=Path(root or Path.cwd()).resolve()
    paths={
        "osn076":base/"qseries_v2/oracle_source_network/state/osn076_production_surface_foundation.json",
        "osn077":base/"qseries_v2/oracle_source_network/state/osn077_uniform_provider_contract.json",
        "osn078":base/"qseries_v2/oracle_source_network/state/osn078_six_league_uniform_physical_gate.json",
        "osn079":base/"qseries_v2/oracle_source_network/state/osn079_uniform_runtime_bindings.json",
    }
    data={}
    for name,p in paths.items():
        if not p.exists():
            raise RuntimeError(f"missing {name} state: {p}")
        data[name]=json.loads(p.read_text(encoding="utf-8"))

    if tuple(x["league"] for x in data["osn076"]["rows"]) != ("NHL","MLS","EPL"):
        raise RuntimeError("OSN-076 source foundation mismatch")
    if tuple(x["league"] for x in data["osn077"]["rows"]) != ADMITTED:
        raise RuntimeError("OSN-077 provider admission mismatch")
    if tuple(x["league"] for x in data["osn078"]["rows"]) != ADMITTED:
        raise RuntimeError("OSN-078 physical gate admission mismatch")
    if tuple(x["league"] for x in data["osn079"]["bindings"]) != ADMITTED:
        raise RuntimeError("OSN-079 runtime binding admission mismatch")

    if not all(int(x["events"]) > 0 for x in data["osn077"]["rows"]):
        raise RuntimeError("OSN-077 contains zero-event provider")
    if not all(int(x["events"]) > 0 for x in data["osn078"]["rows"]):
        raise RuntimeError("OSN-078 contains zero-event physical row")
    if not all(bool(x["direct_runtime_callable_bound"]) for x in data["osn079"]["bindings"]):
        raise RuntimeError("OSN-079 contains unbound runtime callable")

    return SportsSourceFoundationCertification(
        osn076_executable_source_foundation=True,
        osn077_uniform_canonical_provider=True,
        osn078_six_league_physical_gate=True,
        osn079_uniform_runtime_binding=True,
        admitted=ADMITTED,
        held=("NCAAB","MLB_CANONICAL_EVENT_EXTRACTION_CERT_REQUIRED"),
        blocked=("UCL",),
        terminal_dependency="NONE",
        source_foundation_ready=True,
        persistence_activation_next=True,
        continuous_worker_activation_next=False,
        execution_authority=False,
    )
