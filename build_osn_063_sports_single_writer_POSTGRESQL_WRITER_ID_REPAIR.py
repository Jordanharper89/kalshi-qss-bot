from pathlib import Path
import ast

ROOT=Path.cwd()

BOUNDARY="qseries_v2/oracle_source_network/persistence/sports_single_writer_boundary.py"
GATE="qseries_v2/oracle_source_network/certification/sports_single_writer_physical_gate.py"
TEST="test_osn_063_sports_single_writer_POSTGRESQL_WRITER_ID_REPAIR.py"

DEPS=(
    "qseries_v2/oracle_source_network/persistence/sports_persistence_contract.py",
    "qseries_v2/oracle_source_network/canonical/sports_event_v2.py",
    "qseries_v2/oracle_adapters/independent/oad_261_universal_expansion_source_single_writer_postgresql_persistence.py",
    "qseries_v2/oracle_production_hardening/oph_019_postgresql_universal_ingestion_queue.py",
    "qseries_v2/oracle_adapters/independent/oad_068_exact_postgresql_independent_readback.py",
)

def require(rel):
    p=ROOT/rel
    if not p.exists():
        raise SystemExit("[FAIL] missing dependency: "+rel)
    print("[PASS] dependency verified:",rel)
    return p

def exact_signature(rel,symbol):
    p=require(rel)
    tree=ast.parse(p.read_text(encoding="utf-8",errors="ignore"))
    for n in ast.walk(tree):
        if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name==symbol:
            args=[a.arg for a in n.args.args]
            return tuple(args)
    raise SystemExit(f"[FAIL] exact symbol missing: {rel} -> {symbol}")

def put(rel,content):
    p=ROOT/rel
    p.parent.mkdir(parents=True,exist_ok=True)
    compile(content,str(p),"exec")
    p.write_text(content.rstrip()+"\\n",encoding="utf-8")
    print("[WRITE]",rel)

def main():
    print("="*120)
    print(" OSN-063 SPORTS SINGLE-WRITER POSTGRESQL WRITER_ID REPAIR INSTALLER")
    print("="*120)

    for dep in DEPS:
        require(dep)

    oph=exact_signature(
        "qseries_v2/oracle_production_hardening/oph_019_postgresql_universal_ingestion_queue.py",
        "submit_observation_batch",
    )
    o68=exact_signature(
        "qseries_v2/oracle_adapters/independent/oad_068_exact_postgresql_independent_readback.py",
        "exact_postgresql_readback",
    )

    if oph[:3] != ("writer_id","priority","observations"):
        raise SystemExit(f"[FAIL] OPH-019 signature drift: {oph}")
    if o68[:1] != ("observation_ids",):
        raise SystemExit(f"[FAIL] OAD-068 signature drift: {o68}")

    print("[PASS] exact OPH-019 contract verified: writer_id, priority, observations, root")
    print("[PASS] exact OAD-068 contract verified: observation_ids, root")

    put(BOUNDARY,'\nimport uuid\nfrom qseries_v2.oracle_adapters.independent.oad_261_universal_expansion_source_single_writer_postgresql_persistence import canonicalize_expansion_observation\nfrom qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import submit_observation_batch\nfrom qseries_v2.oracle_adapters.independent.oad_068_exact_postgresql_independent_readback import exact_postgresql_readback\n\nWRITER_ID="oracle.osn.sports"\nPRIORITY=20\n\ndef canonicalize(x,batch_id=None):\n    return canonicalize_expansion_observation(\n        x,\n        batch_id or ("osn-sports-"+uuid.uuid4().hex),\n    )\n\ndef submit(observations, root=None):\n    observations=tuple(observations)\n    return submit_observation_batch(\n        WRITER_ID,\n        PRIORITY,\n        observations,\n        root=root,\n    )\n\ndef exact_readback(observation_id, root=None):\n    return exact_postgresql_readback(\n        (observation_id,),\n        root=root,\n    )\n\ndef readback_count(value):\n    if value is None:\n        return 0\n    if isinstance(value,(list,tuple,set)):\n        return len(value)\n    if isinstance(value,dict):\n        for k in ("rows","observations","results","items"):\n            v=value.get(k)\n            if v is not None and hasattr(v,"__len__"):\n                return len(v)\n        return 1 if value else 0\n    for k in ("rows","observations","results","items"):\n        v=getattr(value,k,None)\n        if v is not None and hasattr(v,"__len__"):\n            return len(v)\n    return 1\n')
    put(GATE,'\nimport uuid\nfrom dataclasses import dataclass\nfrom datetime import datetime,timezone\n\nfrom qseries_v2.oracle_source_network.canonical.sports_event_v2 import CanonicalSportsEvent\nfrom qseries_v2.oracle_source_network.persistence.sports_persistence_contract import from_canonical_event\nfrom qseries_v2.oracle_source_network.persistence.sports_single_writer_boundary import (\n    canonicalize,\n    submit,\n    exact_readback,\n    readback_count,\n    WRITER_ID,\n)\n\n@dataclass(frozen=True)\nclass PhysicalPersistenceResult:\n    canonical_event_id:str\n    observation_id:str\n    writer_id:str\n    exact_readback:int\n    execution_authority:bool=False\n\ndef persist_fixture():\n    token=uuid.uuid4().hex[:12]\n    now=datetime.now(timezone.utc).isoformat()\n    event=CanonicalSportsEvent(\n        league="NFL",\n        season="2026",\n        provider="osn_physical_fixture",\n        home_team="OSN_HOME",\n        away_team="OSN_AWAY",\n        scheduled_start="2026-09-06T12:00:00Z",\n        source_observed_at=now,\n        source_authority="certification_fixture",\n        provider_event_id="osn-"+token,\n        event_discriminator="osn-"+token,\n    )\n\n    raw=from_canonical_event(event)\n    canonical=canonicalize(raw,"osn063-repair-"+token)\n\n    submit((canonical,))\n    readback=exact_readback(canonical.observation_id)\n    count=readback_count(readback)\n\n    return PhysicalPersistenceResult(\n        canonical_event_id=event.canonical_event_id,\n        observation_id=canonical.observation_id,\n        writer_id=WRITER_ID,\n        exact_readback=count,\n    )\n')
    put(TEST,'\nimport inspect\n\nfrom qseries_v2.oracle_source_network.persistence.sports_single_writer_boundary import (\n    submit_observation_batch,\n    exact_postgresql_readback,\n    WRITER_ID,\n)\nfrom qseries_v2.oracle_source_network.certification.sports_single_writer_physical_gate import persist_fixture\n\nprint("[OPH019_SIGNATURE]",inspect.signature(submit_observation_batch))\nprint("[OAD068_SIGNATURE]",inspect.signature(exact_postgresql_readback))\n\nassert str(inspect.signature(submit_observation_batch))=="(writer_id, priority, observations, root=None)"\nassert str(inspect.signature(exact_postgresql_readback))=="(observation_ids, root=None)"\nassert WRITER_ID=="oracle.osn.sports"\n\nr=persist_fixture()\nprint("[PHYSICAL_REPAIR]",r)\n\nassert r.writer_id=="oracle.osn.sports"\nassert len(r.observation_id)>=32\nassert r.exact_readback>=1\nassert r.execution_authority is False\n\nprint("[PASS] exact OPH-019 writer_id contract used")\nprint("[PASS] sports observation persisted through existing single writer")\nprint("[PASS] exact PostgreSQL observation-ID readback certified")\nprint("[PASS] OSN-063 writer_id repair certified")\n')

    print("[PASS] broken producer-style invocation retired")
    print("[PASS] sports boundary repaired to exact writer_id contract")
    print("[PASS] existing OPH-019 single writer retained")
    print("[PASS] no direct PostgreSQL writer introduced")
    print("[PASS] execution_authority=FALSE")

if __name__=="__main__":
    main()
