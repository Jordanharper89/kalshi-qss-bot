from pathlib import Path
import importlib,os,subprocess,sys
ROOT=Path.cwd().resolve(); PKG=ROOT/"qseries_v2"/"oracle_production_hardening"
MOD=PKG/"oph_002_priority_observation_ingestion_queue.py"; TEST=ROOT/"test_oph_002_priority_observation_ingestion_queue.py"; INIT=PKG/"__init__.py"
MODULE='from dataclasses import dataclass\nPRIORITIES={"FAST_LANE":100,"LIVE_ADAPTER":80,"NORMAL":60,"COVERAGE":20,"BACKFILL":10}\n\n@dataclass(frozen=True)\nclass ObservationAdmission:\n    adapter_id:str; lane:str; priority:int; observations:tuple; read_only_intelligence:bool=True; execution_authority:bool=False\n\ndef priority_for_lane(lane):\n    key=str(lane).strip().upper()\n    if key not in PRIORITIES: raise ValueError(f"unsupported ingestion lane: {lane}")\n    return PRIORITIES[key]\n\ndef admit_observations(adapter_id,lane,observations):\n    items=tuple(observations)\n    if not adapter_id: raise ValueError("adapter_id required")\n    if not items: raise ValueError("observations required")\n    return ObservationAdmission(str(adapter_id),str(lane).strip().upper(),priority_for_lane(lane),items,True,False)\n\ndef verify_oph_002_priority_observation_ingestion_queue():\n    a=admit_observations("kalshi.fast","FAST_LANE",("x",)); b=admit_observations("kalshi.coverage","COVERAGE",("y",))\n    return a.priority>b.priority and a.read_only_intelligence and not a.execution_authority\n'; TESTSRC='import unittest\nfrom qseries_v2.oracle_production_hardening.oph_002_priority_observation_ingestion_queue import verify_oph_002_priority_observation_ingestion_queue\nclass T(unittest.TestCase):\n    def test_verifier(self): self.assertTrue(verify_oph_002_priority_observation_ingestion_queue())\nif __name__=="__main__":\n    print("="*80); print(" OPH-002 CERTIFICATION TEST"); print(" PRIORITY OBSERVATION INGESTION QUEUE"); print("="*80)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] OPH-002 certified"); print("[DONE] OPH-002 CERTIFIED")\n'
def write_exact(p,s):
    p.parent.mkdir(parents=True,exist_ok=True); t=p.with_suffix(p.suffix+".tmp"); t.write_text(s,encoding="utf-8",newline="\n"); os.replace(t,p)
def main():
    print("="*80); print(" OPH-002 INSTALLER"); print(" PRIORITY OBSERVATION INGESTION QUEUE"); print("="*80); print("[ROOT]",ROOT)
    sys.path.insert(0,str(ROOT)); up=importlib.import_module("qseries_v2.oracle_production_hardening.oph_001_single_canonical_writer_service")
    if up.verify_oph_001_single_canonical_writer_service() is not True: raise RuntimeError("OPH-001 verification failed")
    print("[PASS] Certified OPH-001 upstream boundary verified")
    affected=(MOD,TEST,INIT); old={p:(p.read_bytes() if p.exists() else None) for p in affected}
    try:
        write_exact(MOD,MODULE); write_exact(TEST,TESTSRC)
        cur=INIT.read_text(encoding="utf-8") if INIT.exists() else ""; ex="from .oph_002_priority_observation_ingestion_queue import *"
        if ex not in cur: write_exact(INIT,cur.rstrip()+"\n"+ex+"\n")
        subprocess.run([sys.executable,str(TEST)],cwd=str(ROOT),check=True)
    except Exception:
        for p,b in old.items():
            if b is None:
                if p.exists(): p.unlink()
            else: p.write_bytes(b)
        print("[ROLLBACK] OPH-002 installation failed"); raise
    print("[PASS] Wrote:",MOD.relative_to(ROOT)); print("[PASS] Wrote:",TEST.name); print("[DONE] OPH-002 INSTALLATION AND CERTIFICATION COMPLETE")
if __name__=="__main__": main()
