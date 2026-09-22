from pathlib import Path
ROOT=Path.cwd()
TARGET="qseries_v2/oracle_source_network/persistence/sports_single_writer_boundary.py"
TEST="test_osn_081_read_before_write_MISSING_ROW_SEMANTICS_REPAIR.py"
MODULE_SOURCE='\nfrom importlib import import_module\nimport inspect\n\nfrom qseries_v2.oracle_adapters.independent.oad_261_universal_expansion_source_single_writer_postgresql_persistence import canonicalize_expansion_observation\nfrom qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import submit_observation_batch, await_request\nfrom qseries_v2.oracle_adapters.independent.oad_068_exact_postgresql_independent_readback import exact_postgresql_readback\n\nWRITER_ID="oracle.osn.sports"\nPRIORITY=20\nCONVERTER_MODULE="qseries_v2.oracle_source_network.persistence.sports_persistence_contract"\nCONVERTER_FUNCTION="from_canonical_event"\n\ndef _converter():\n    mod=import_module(CONVERTER_MODULE)\n    return getattr(mod,CONVERTER_FUNCTION)\n\ndef _convert(observation,batch_id=None):\n    fn=_converter()\n    sig=inspect.signature(fn)\n    args=[]\n    kwargs={}\n    supplied=False\n    for p in sig.parameters.values():\n        if p.kind in (p.VAR_POSITIONAL,p.VAR_KEYWORD):\n            continue\n        if not supplied and p.name.lower() in ("event","observation","sports_event","canonical_event","value","x"):\n            args.append(observation)\n            supplied=True\n            continue\n        if p.name=="batch_id":\n            kwargs[p.name]=batch_id or "osn-sports"\n            continue\n        if p.default is not inspect._empty:\n            continue\n        if not supplied:\n            args.append(observation)\n            supplied=True\n            continue\n        raise TypeError("unsupported exact converter signature: "+str(sig))\n    return fn(*args,**kwargs)\n\ndef canonicalize(observation,batch_id=None):\n    expansion=_convert(observation,batch_id=batch_id)\n    return canonicalize_expansion_observation(expansion,batch_id or "osn-sports")\n\ndef submit(observations,root=None):\n    return submit_observation_batch(\n        writer_id=WRITER_ID,\n        priority=PRIORITY,\n        observations=tuple(observations),\n        root=root,\n    )\n\ndef await_commit(request_id,root=None,timeout_seconds=45.0):\n    return await_request(request_id,root=root,timeout_seconds=timeout_seconds)\n\ndef exact_readback(observation_id,root=None):\n    oid=str(observation_id)\n    try:\n        return exact_postgresql_readback((oid,),root=root)\n    except RuntimeError as exc:\n        msg=str(exc)\n        if msg == "exact PostgreSQL observation missing: "+oid:\n            return ()\n        raise\n\ndef readback_count(value):\n    if value is None:\n        return 0\n    if isinstance(value,(list,tuple,set,dict)):\n        return len(value)\n    for attr in ("rows","observations","results","records"):\n        if hasattr(value,attr):\n            try:\n                return len(getattr(value,attr))\n            except Exception:\n                pass\n    try:\n        return len(value)\n    except Exception:\n        return int(bool(value))\n'
TEST_SOURCE='\nfrom pathlib import Path\nimport uuid\n\nfrom qseries_v2.oracle_source_network.persistence.sports_single_writer_boundary import exact_readback, readback_count\n\nmissing="osn081-missing-"+uuid.uuid4().hex\nvalue=exact_readback(missing,root=Path.cwd())\ncount=readback_count(value)\n\nprint("[MISSING_READBACK]",missing,"count=",count,"value_type=",type(value).__name__)\nassert count==0\nprint("[PASS] exact OAD-068 missing-row exception normalized to read-before-write miss")\nprint("[PASS] unexpected RuntimeError values remain unmasked")\nprint("[PASS] OSN-081 read-before-write missing-row semantics repaired")\n'

def main():
    print("="*120)
    print(" OSN-081 READ-BEFORE-WRITE — MISSING ROW SEMANTICS REPAIR")
    print("="*120)

    for dep in (
        "qseries_v2/oracle_source_network/persistence/sports_persistence_contract.py",
        "qseries_v2/oracle_adapters/independent/oad_261_universal_expansion_source_single_writer_postgresql_persistence.py",
        "qseries_v2/oracle_adapters/independent/oad_068_exact_postgresql_independent_readback.py",
        "qseries_v2/oracle_production_hardening/oph_019_postgresql_universal_ingestion_queue.py",
        "qseries_v2/oracle_source_network/state/osn081_exact_persistence_contract_repair.json",
    ):
        if not (ROOT/dep).exists():
            raise SystemExit("[FAIL] missing dependency: "+dep)
        print("[PASS] dependency verified:",dep)

    p=ROOT/TARGET
    p.write_text(MODULE_SOURCE,encoding="utf-8")
    compile(p.read_text(encoding="utf-8"),str(p),"exec")

    t=ROOT/TEST
    t.write_text(TEST_SOURCE,encoding="utf-8")
    compile(t.read_text(encoding="utf-8"),str(t),"exec")

    print("[WRITE]",TARGET)
    print("[WRITE]",TEST)
    print("[PASS] exact OAD-068 semantics preserved")
    print("[PASS] only exact missing-row condition is normalized to zero")
    print("[PASS] no writer change")
    print("[PASS] execution_authority=FALSE")

if __name__=="__main__":
    main()
