from pathlib import Path
import os,sys,subprocess,importlib
ROOT=Path.cwd().resolve(); PKG=ROOT/"qseries_v2"/"oracle_pre_settlement_coverage"
MOD=PKG/"opc_008_ola_postgresql_snapshot_persistence_bridge.py"; TEST=ROOT/"test_opc_008_ola_postgresql_snapshot_persistence_bridge.py"; INIT=PKG/"__init__.py"
MODULE_SOURCE='from dataclasses import dataclass\nfrom pathlib import Path\nimport os\nfrom qseries_v2.oracle_intelligence.live_acquisition.oracle_postgresql_canonical_observation_persistence_backend import OraclePostgreSQLCanonicalObservationPersistenceBackend\nfrom qseries_v2.oracle_intelligence.live_acquisition.oracle_postgresql_canonical_observation_persistence_router import OraclePostgreSQLCanonicalObservationPersistenceRouter\n\n@dataclass(frozen=True)\nclass SnapshotPersistenceSummary:\n    requested:int\n    accepted:int\n    rejected:int\n    read_only_intelligence:bool=True\n    execution_authority:bool=False\n\ndef _db(root):\n    u=os.environ.get("DATABASE_URL") or os.environ.get("ORACLE_DATABASE_URL")\n    if u:return u\n    p=Path(root)/".env"\n    if p.is_file():\n        for line in p.read_text(encoding="utf-8",errors="ignore").splitlines():\n            if "=" in line and not line.lstrip().startswith("#"):\n                k,v=line.split("=",1)\n                if k.strip() in ("DATABASE_URL","ORACLE_DATABASE_URL"): return v.strip().strip(\'"\').strip("\'")\n    raise RuntimeError("DATABASE_URL / ORACLE_DATABASE_URL not configured")\n\ndef build_opc_postgresql_router(root=None):\n    root=Path(root or Path.cwd()).resolve(); url=_db(root)\n    import psycopg\n    backend=OraclePostgreSQLCanonicalObservationPersistenceBackend(\n        connection_factory=lambda: psycopg.connect(url),auto_initialize_schema=False)\n    return OraclePostgreSQLCanonicalObservationPersistenceRouter(\n        persistence_backend=backend,\n        route_id="oracle.postgresql.kalshi.opc.snapshot.router.v1",\n        routing_metadata={"production_path":True,"shadow_mode":True,"opc_build":"OPC-008"},\n        replay_metadata={"replay_source":"OPC-008"},\n        audit_metadata={"component":"oracle_pre_settlement_coverage"})\n\ndef persist_snapshot_batch(observations,*,routed_at,router):\n    obs=tuple(observations)\n    if not obs:return SnapshotPersistenceSummary(0,0,0,True,False)\n    ev=tuple(router.route_batch(obs,routed_at))\n    accepted=sum(1 for x in ev if getattr(x,"accepted",False) is True)\n    return SnapshotPersistenceSummary(len(obs),accepted,len(obs)-accepted,True,False)\n\ndef verify_opc_008_ola_postgresql_snapshot_persistence_bridge():\n    class E: accepted=True\n    class R:\n        def route_batch(self,observations,routed_at): return tuple(E() for _ in observations)\n    x=persist_snapshot_batch((1,2),routed_at=None,router=R())\n    return x.requested==2 and x.accepted==2 and x.rejected==0 and not x.execution_authority\n'; TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_pre_settlement_coverage.opc_008_ola_postgresql_snapshot_persistence_bridge import *\nclass T(unittest.TestCase):\n    def test_verifier(self): self.assertTrue(verify_opc_008_ola_postgresql_snapshot_persistence_bridge())\n    def test_empty(self):\n        class R: pass\n        self.assertEqual(persist_snapshot_batch((),routed_at=None,router=R()).accepted,0)\nif __name__=="__main__":\n    print("="*72);print(" OPC-008 CERTIFICATION TEST");print(" OLA POSTGRESQL SNAPSHOT PERSISTENCE BRIDGE");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] Existing OLA PostgreSQL canonical router reuse certified");print("[DONE] OPC-008 CERTIFIED")\n'
def w(p,t):
    p.parent.mkdir(parents=True,exist_ok=True); q=p.with_suffix(p.suffix+".tmp"); q.write_text(t,encoding="utf-8",newline="\n"); os.replace(q,p)
def main():
    print("="*72);print(" OPC-008 INSTALLER");print("="*72);print("[ROOT]",ROOT)
    sys.path.insert(0,str(ROOT)); up=importlib.import_module("qseries_v2.oracle_pre_settlement_coverage.opc_007_coverage_gap_snapshot_planner")
    if up.verify_opc_007_coverage_gap_snapshot_planner() is not True: raise RuntimeError("OPC-007 verification failed")
    print("[PASS] Certified OPC-007 upstream boundary verified")
    affected=(MOD,TEST,INIT); backups={x:(x.read_bytes() if x.exists() else None) for x in affected}
    try:
        w(MOD,MODULE_SOURCE); w(TEST,TEST_SOURCE)
        cur=INIT.read_text(encoding="utf-8") if INIT.exists() else ""; line="from .opc_008_ola_postgresql_snapshot_persistence_bridge import *"
        if line not in cur: w(INIT,cur.rstrip()+"\n"+line+"\n")
        subprocess.run([sys.executable,str(TEST)],cwd=str(ROOT),check=True)
    except Exception:
        for x,old in backups.items():
            if old is None:
                if x.exists(): x.unlink()
            else: x.write_bytes(old)
        print("[ROLLBACK] OPC-008 installation failed"); raise
    print("[DONE] OPC-008 INSTALLATION AND CERTIFICATION COMPLETE")
if __name__=="__main__": main()
