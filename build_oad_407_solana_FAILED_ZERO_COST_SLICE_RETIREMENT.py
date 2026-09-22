from pathlib import Path
import hashlib,json,shutil,time
EXPECTED='build_oad_407_solana_FAILED_ZERO_COST_SLICE_RETIREMENT.py'
MODULES=[('qseries_v2/oracle_adapters/independent/oad_393_solana_zero_cost_public_rpc_budget_governor.py', 'ff4207a4151ac99a73aa819679cb0d6a221eb8917fb87fbbc83f90b903201d22'), ('qseries_v2/oracle_adapters/independent/oad_394_solana_finalized_head_missing_slot_scheduler.py', '661adcc22af829fa478e43ca6f3c38059c5ad170a765d4abc625af5e4e04702c'), ('qseries_v2/oracle_adapters/independent/oad_395_solana_block_efficient_universal_acquisition_worker.py', 'cf6f13b94de9c10b5c2ed4bbfe242360ef0f7a086932581202989528eb6eca6d'), ('qseries_v2/oracle_adapters/independent/oad_396_solana_websocket_assisted_live_head.py', '6bb2a5b495d5cd4c2bbcfe36fdc74501927d46df25505e0fb1f4bbb06cca161f'), ('qseries_v2/oracle_adapters/independent/oad_397_solana_zero_cost_universal_surveillance_control_plane.py', '774815d0d7a103e7d35e27fd971157fa4e7de4ec03f8daa6a07ea2272dd33af4'), ('qseries_v2/oracle_adapters/independent/oad_398_solana_zero_cost_governed_worker_cycle.py', '8c8cb251d2df4219d091d29a661af1d38110e7ac88a0812376be022e6257477d'), ('qseries_v2/oracle_adapters/independent/oad_399_solana_zero_cost_continuous_surveillance_worker.py', 'fa5d65df788d03ba1a32799d363ccc4035fd17f9bc622ff8d98b12b3a1ea9fe2'), ('qseries_v2/oracle_adapters/independent/oad_400_solana_live_coverage_telemetry.py', '1275af70a8b878cbff5c7bda416e1a2adb5e8c74721f567da8ce9f9ceb39aec0'), ('qseries_v2/oracle_adapters/independent/oad_401_solana_zero_cost_catchup_recovery_controller.py', '8c58e4da6f6b1112c2b5f5383169615fe340fa5497b0d68159cf0bce5e70f994'), ('qseries_v2/oracle_adapters/independent/oad_402_solana_zero_cost_surveillance_physical_gate.py', '1f073486799a79277d98f6390f8315f6e9a9c5d3e91c58e87483f46f9b68b056'), ('qseries_v2/oracle_adapters/independent/oad_403_solana_oph019_021_ingestion_completion_audit.py', '20142a5dd0c41e146985ebdc73f029ffc54ae5b407faa4246c65840ae2b9708f'), ('qseries_v2/oracle_adapters/independent/oad_404_solana_postgresql_queue_writer_live_state_audit.py', '9d061cdfc146e05157ff7ea86d2308eaa49999527fe77902718479f939c9f839'), ('qseries_v2/oracle_adapters/independent/oad_405_solana_stale_oph021_writer_lease_recovery_activation.py', '793f8d7d5a7f62b937d08e42966c74f01a515dad2ac7455c97b3281b03155acc'), ('qseries_v2/oracle_adapters/independent/oad_406_solana_oph021_advisory_writer_recovery_certification.py', '798cac966771e4a438eecff66a4e69a66a765bb18771121761422c84f14f4aa3')]
INIT=Path("qseries_v2/oracle_adapters/independent/__init__.py")
INIT_HASH='c3f4365ffc57946213eacf86d0b4b2967cbae3a5b5b25fd2cc09d003b0acd57b'
TEST_SOURCE='import importlib, json, unittest\nfrom pathlib import Path\nclass T(unittest.TestCase):\n    def test_failed_slice_not_active(self):\n        d=Path.cwd()/"qseries_v2/oracle_adapters/independent"\n        for n in range(393,407): self.assertEqual(list(d.glob(f"oad_{n}_*.py")),[])\n    def test_package_imports(self): self.assertIsNotNone(importlib.import_module("qseries_v2.oracle_adapters.independent"))\n    def test_manifest(self):\n        hits=sorted((Path.cwd()/"retired").glob("solana_failed_zero_cost_slice_393_406.*/RETIREMENT_MANIFEST.json")); self.assertTrue(hits)\n        x=json.loads(hits[-1].read_text()); self.assertEqual(x["state"],"RETIRED_FAILED_PRODUCTION_SLICE"); self.assertFalse(x["execution_authority"])\nif __name__=="__main__":\n    rr=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not rr.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] OAD-407 failed Solana zero-cost slice retired")\n'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    if Path(__file__).name!=EXPECTED: raise RuntimeError("installer filename mismatch")
    root=Path.cwd().resolve()
    if not (root/"qseries_v2").is_dir(): raise RuntimeError("run from repository root")
    for rel,h in MODULES:
        p=root/rel
        if not p.is_file() or sha(p)!=h: raise RuntimeError("active failed-slice source mismatch: "+rel)
    ip=root/INIT
    if sha(ip)!=INIT_HASH: raise RuntimeError("independent __init__ source mismatch")
    stamp=time.strftime("%Y%m%dT%H%M%S")
    archive=root/"retired"/("solana_failed_zero_cost_slice_393_406."+stamp); archive.mkdir(parents=True)
    moved=[]
    for rel,_ in MODULES:
        src=root/rel; dst=archive/rel; dst.parent.mkdir(parents=True,exist_ok=True); shutil.move(src,dst); moved.append(rel)
    for pat in ("run_oad_399_*.py","run_oad_402_*.py","test_oad_393_*.py","test_oad_394_*.py","test_oad_395_*.py","test_oad_396_*.py","test_oad_397_*.py","test_oad_398_*.py","test_oad_399_*.py","test_oad_400_*.py","test_oad_401_*.py","test_oad_402_*.py","test_oad_403_*.py","test_oad_404_*.py","test_oad_405_*.py","test_oad_406_*.py"):
        for src in root.glob(pat): shutil.move(src,archive/src.name); moved.append(src.name)
    lines=[line for line in ip.read_text(encoding="utf-8").splitlines() if not any(f".oad_{n}_" in line for n in range(393,407))]
    ip.write_text("\n".join(lines)+"\n",encoding="utf-8",newline="\n")
    manifest={"state":"RETIRED_FAILED_PRODUCTION_SLICE","range":"OAD-393..OAD-406","reason":"control path could not keep persisted checkpoint pace with finalized Solana head","moved":moved,"execution_authority":False}
    (archive/"RETIREMENT_MANIFEST.json").write_text(json.dumps(manifest,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    (root/"test_oad_407_solana_failed_zero_cost_slice_retirement.py").write_text(TEST_SOURCE,encoding="utf-8",newline="\n")
    print("[PASS] exact active OAD-393..406 repo sources matched")
    print("[PASS] failed slice removed from active package and archived for rollback")
    print("[PASS] rollback archive:",archive.relative_to(root))
    print("[PASS] execution_authority=FALSE")
    print("[DONE]",EXPECTED)
if __name__=="__main__": main()
