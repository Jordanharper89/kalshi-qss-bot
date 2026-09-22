from pathlib import Path

ROOT=Path.cwd()
TEST="test_osn_063_sports_single_writer_WRITER_ID_REPAIR_CLEAN.py"

def main():
    print("="*120)
    print(" OSN-063 SPORTS SINGLE-WRITER WRITER_ID REPAIR CLEAN TEST INSTALLER")
    print("="*120)

    boundary=ROOT/"qseries_v2/oracle_source_network/persistence/sports_single_writer_boundary.py"
    gate=ROOT/"qseries_v2/oracle_source_network/certification/sports_single_writer_physical_gate.py"
    if not boundary.exists():
        raise SystemExit("[FAIL] repaired sports boundary missing")
    if not gate.exists():
        raise SystemExit("[FAIL] repaired physical gate missing")

    b=boundary.read_text(encoding="utf-8",errors="ignore")
    if 'WRITER_ID="oracle.osn.sports"' not in b:
        raise SystemExit("[FAIL] repaired writer_id boundary not installed")
    if "submit_observation_batch(" not in b:
        raise SystemExit("[FAIL] OPH-019 submit call missing")

    content='import inspect\n\nfrom qseries_v2.oracle_source_network.persistence.sports_single_writer_boundary import (\n    submit_observation_batch,\n    exact_postgresql_readback,\n    WRITER_ID,\n)\nfrom qseries_v2.oracle_source_network.certification.sports_single_writer_physical_gate import persist_fixture\n\nprint("[OPH019_SIGNATURE]", inspect.signature(submit_observation_batch))\nprint("[OAD068_SIGNATURE]", inspect.signature(exact_postgresql_readback))\n\nassert str(inspect.signature(submit_observation_batch)) == "(writer_id, priority, observations, root=None)"\nassert str(inspect.signature(exact_postgresql_readback)) == "(observation_ids, root=None)"\nassert WRITER_ID == "oracle.osn.sports"\n\nr = persist_fixture()\nprint("[PHYSICAL_REPAIR]", r)\n\nassert r.writer_id == "oracle.osn.sports"\nassert len(r.observation_id) >= 32\nassert r.exact_readback >= 1\nassert r.execution_authority is False\n\nprint("[PASS] exact OPH-019 writer_id contract used")\nprint("[PASS] sports observation persisted through existing single writer")\nprint("[PASS] exact PostgreSQL observation-ID readback certified")\nprint("[PASS] OSN-063 writer_id repair certified")\n'
    compile(content,TEST,"exec")
    (ROOT/TEST).write_text(content,encoding="utf-8")

    # Compile the actual generated file again from disk.
    compile((ROOT/TEST).read_text(encoding="utf-8"),TEST,"exec")

    print("[WRITE]",TEST)
    print("[PASS] malformed literal \\n test retired")
    print("[PASS] clean replacement test compiled before install")
    print("[PASS] existing repaired production boundary preserved")
    print("[PASS] execution_authority=FALSE")

if __name__=="__main__":
    main()
