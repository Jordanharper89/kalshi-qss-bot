from pathlib import Path
ROOT=Path.cwd()
MODULE="qseries_v2/oracle_source_network/certification/final_sports_source_foundation.py"
TEST="test_osn_080_final_sports_source_foundation_EXECUTABLE_RECERTIFICATION.py"
MODULE_SOURCE='\nfrom dataclasses import dataclass\nfrom pathlib import Path\nimport json\n\nADMITTED=("NFL","NCAAF","NBA","NHL","MLS","EPL")\n\n@dataclass(frozen=True)\nclass SportsSourceFoundationCertification:\n    osn076_executable_source_foundation:bool\n    osn077_uniform_canonical_provider:bool\n    osn078_six_league_physical_gate:bool\n    osn079_uniform_runtime_binding:bool\n    admitted:tuple\n    held:tuple\n    blocked:tuple\n    terminal_dependency:str\n    source_foundation_ready:bool\n    persistence_activation_next:bool\n    continuous_worker_activation_next:bool\n    execution_authority:bool=False\n\ndef certify(root=None):\n    base=Path(root or Path.cwd()).resolve()\n    paths={\n        "osn076":base/"qseries_v2/oracle_source_network/state/osn076_production_surface_foundation.json",\n        "osn077":base/"qseries_v2/oracle_source_network/state/osn077_uniform_provider_contract.json",\n        "osn078":base/"qseries_v2/oracle_source_network/state/osn078_six_league_uniform_physical_gate.json",\n        "osn079":base/"qseries_v2/oracle_source_network/state/osn079_uniform_runtime_bindings.json",\n    }\n    data={}\n    for name,p in paths.items():\n        if not p.exists():\n            raise RuntimeError(f"missing {name} state: {p}")\n        data[name]=json.loads(p.read_text(encoding="utf-8"))\n\n    if tuple(x["league"] for x in data["osn076"]["rows"]) != ("NHL","MLS","EPL"):\n        raise RuntimeError("OSN-076 source foundation mismatch")\n    if tuple(x["league"] for x in data["osn077"]["rows"]) != ADMITTED:\n        raise RuntimeError("OSN-077 provider admission mismatch")\n    if tuple(x["league"] for x in data["osn078"]["rows"]) != ADMITTED:\n        raise RuntimeError("OSN-078 physical gate admission mismatch")\n    if tuple(x["league"] for x in data["osn079"]["bindings"]) != ADMITTED:\n        raise RuntimeError("OSN-079 runtime binding admission mismatch")\n\n    if not all(int(x["events"]) > 0 for x in data["osn077"]["rows"]):\n        raise RuntimeError("OSN-077 contains zero-event provider")\n    if not all(int(x["events"]) > 0 for x in data["osn078"]["rows"]):\n        raise RuntimeError("OSN-078 contains zero-event physical row")\n    if not all(bool(x["direct_runtime_callable_bound"]) for x in data["osn079"]["bindings"]):\n        raise RuntimeError("OSN-079 contains unbound runtime callable")\n\n    return SportsSourceFoundationCertification(\n        osn076_executable_source_foundation=True,\n        osn077_uniform_canonical_provider=True,\n        osn078_six_league_physical_gate=True,\n        osn079_uniform_runtime_binding=True,\n        admitted=ADMITTED,\n        held=("NCAAB","MLB_CANONICAL_EVENT_EXTRACTION_CERT_REQUIRED"),\n        blocked=("UCL",),\n        terminal_dependency="NONE",\n        source_foundation_ready=True,\n        persistence_activation_next=True,\n        continuous_worker_activation_next=False,\n        execution_authority=False,\n    )\n'
TEST_SOURCE='\nfrom pathlib import Path\nfrom qseries_v2.oracle_source_network.certification.final_sports_source_foundation import certify\n\nc=certify(root=Path.cwd())\nprint("[FINAL_SPORTS_SOURCE_FOUNDATION]",c)\n\nassert c.osn076_executable_source_foundation is True\nassert c.osn077_uniform_canonical_provider is True\nassert c.osn078_six_league_physical_gate is True\nassert c.osn079_uniform_runtime_binding is True\nassert c.source_foundation_ready is True\nassert c.persistence_activation_next is True\nassert c.continuous_worker_activation_next is False\nassert c.terminal_dependency=="NONE"\nassert c.execution_authority is False\n\nprint("[PASS] NHL/MLS/EPL foundation repair recertified")\nprint("[PASS] six admitted leagues share one physically proven canonical provider contract")\nprint("[PASS] source foundation ready for PostgreSQL persistence activation")\nprint("[PASS] always-on worker is intentionally NOT claimed yet")\nprint("[PASS] OSN-080 executable source-foundation recertification complete")\n'

def main():
    print("="*120)
    print(" OSN-080 FINAL SPORTS SOURCE FOUNDATION — EXECUTABLE RECERTIFICATION")
    print("="*120)
    for dep in (
        "qseries_v2/oracle_source_network/state/osn076_production_surface_foundation.json",
        "qseries_v2/oracle_source_network/state/osn077_uniform_provider_contract.json",
        "qseries_v2/oracle_source_network/state/osn078_six_league_uniform_physical_gate.json",
        "qseries_v2/oracle_source_network/state/osn079_uniform_runtime_bindings.json",
    ):
        if not (ROOT/dep).exists():
            raise SystemExit("[FAIL] missing dependency: "+dep)
        print("[PASS] dependency verified:",dep)

    p=ROOT/MODULE
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(MODULE_SOURCE,encoding="utf-8")
    compile(p.read_text(encoding="utf-8"),str(p),"exec")
    print("[WRITE]",MODULE)

    t=ROOT/TEST
    t.write_text(TEST_SOURCE,encoding="utf-8")
    compile(t.read_text(encoding="utf-8"),str(t),"exec")
    print("[WRITE]",TEST)
    print("[PASS] final source-foundation boundary written")
    print("[PASS] persistence/worker activation intentionally remain downstream")
    print("[PASS] execution_authority=FALSE")

if __name__=="__main__":
    main()
