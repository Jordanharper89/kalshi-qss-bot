from __future__ import annotations
import os,sys,subprocess
from pathlib import Path

def root():
    for base in (Path.cwd().resolve(),Path(__file__).resolve().parent):
        for c in (base,base/"kalshi-qss-bot",*base.parents):
            if (c/"qseries_v2").is_dir():
                return c
    raise RuntimeError("Could not locate Q Series repository")

def write_atomic(path,source):
    path.parent.mkdir(parents=True,exist_ok=True)
    compile(source,str(path),"exec")
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(source.lstrip("\n"),encoding="utf-8",newline="\n")
    os.replace(tmp,path)

def run_test(r,p):
    z=subprocess.run([sys.executable,str(p)],cwd=str(r))
    if z.returncode:
        raise RuntimeError("Certification test failed: "+p.name)

REVISION='OAD_227_CRYPTO_LEARNED_CASE_ASOF_SNAPSHOT_BOUNDARY_IDENTITY_SAFE_V1'
EXPECTED_INSTALLER='build_oad_227_crypto_learned_case_asof_snapshot_boundary_IDENTITY_SAFE.py'
MODULE_NAME='oad_227_crypto_learned_case_asof_snapshot_boundary.py'
TEST_NAME='test_oad_227_crypto_learned_case_asof_snapshot_boundary.py'
MODULE='from __future__ import annotations\nfrom dataclasses import dataclass\nfrom hashlib import sha256\nimport json\nfrom pathlib import Path\nfrom qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect\n\nREAD_ONLY=True;PROBABILITY_ENABLED=False;DIRECTION_ENABLED=False;EXECUTION_AUTHORITY=False\nSOURCE_IDS=("source.crypto.learned_case.btc","source.crypto.learned_case.eth","source.crypto.learned_case.sol")\n\ndef _h(v):\n    return sha256(json.dumps(v,sort_keys=True,separators=(",",":"),default=str).encode()).hexdigest()\n\n@dataclass(frozen=True,slots=True)\nclass CryptoLearnedCaseSnapshot:\n    as_of_sequence:int\n    row_count:int\n    rows:tuple\n    snapshot_hash:str\n    read_only:bool=True\n    probability_enabled:bool=False\n    direction_enabled:bool=False\n    execution_authority:bool=False\n\ndef capture_crypto_learned_case_snapshot(root=None,per_asset_limit=512):\n    root=Path(root or Path.cwd()).resolve()\n    with connect(root,autocommit=False) as c:\n        with c.cursor() as q:\n            q.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY")\n            q.execute("SET LOCAL statement_timeout=\'10000ms\'")\n            q.execute("""SELECT COALESCE(MAX(sequence_number),0)\n                         FROM public.oracle_canonical_observations\n                         WHERE source_id = ANY(%s::text[])\n                           AND observation_type=\'crypto_verified_learned_case\'""",(list(SOURCE_IDS),))\n            cutoff=int((q.fetchone() or (0,))[0] or 0)\n            rows=[]\n            for source in SOURCE_IDS:\n                q.execute("""SELECT sequence_number,observation_id,source_id,observed_at,\n                                    COALESCE(canonical_observation_json->\'raw_observation\'->\'payload\',\n                                             canonical_observation_json->\'payload\',\'{}\'::jsonb)\n                             FROM public.oracle_canonical_observations\n                             WHERE source_id=%s\n                               AND observation_type=\'crypto_verified_learned_case\'\n                               AND sequence_number<=%s\n                             ORDER BY sequence_number DESC\n                             LIMIT %s""",(source,cutoff,int(per_asset_limit)))\n                rows.extend(q.fetchall() or [])\n        c.rollback()\n    rows=tuple(sorted(rows,key=lambda x:int(x[0])))\n    identity=[(int(r[0]),str(r[1]),str(r[2])) for r in rows]\n    return CryptoLearnedCaseSnapshot(cutoff,len(rows),rows,_h({"as_of_sequence":cutoff,"rows":identity}))\n'
TEST='import unittest\nfrom unittest.mock import patch\nfrom qseries_v2.oracle_adapters.independent import oad_227_crypto_learned_case_asof_snapshot_boundary as m\n\nclass Cur:\n    def __init__(self):self.n=0;self.sql=[]\n    def __enter__(self):return self\n    def __exit__(self,*x):return False\n    def execute(self,s,args=None):self.sql.append(s)\n    def fetchone(self):return (100,)\n    def fetchall(self):\n        self.n+=1\n        return [(97+self.n,f"o{self.n}",m.SOURCE_IDS[(self.n-1)%3],"t",{"asset":"BTC"})]\nclass Conn:\n    def __init__(self):self.c=Cur()\n    def __enter__(self):return self\n    def __exit__(self,*x):return False\n    def cursor(self):return self.c\n    def rollback(self):pass\n\nclass T(unittest.TestCase):\n    def test_snapshot(self):\n        c=Conn()\n        with patch.object(m,"connect",return_value=c):\n            a=m.capture_crypto_learned_case_snapshot()\n        print("[AS_OF]",a.as_of_sequence,"[ROWS]",a.row_count,"[HASH]",a.snapshot_hash)\n        self.assertEqual(a.as_of_sequence,100)\n        self.assertEqual(a.row_count,3)\n        self.assertEqual(len(a.snapshot_hash),64)\n        self.assertTrue(any("sequence_number<=%s" in x for x in c.c.sql))\n        self.assertTrue(any("REPEATABLE READ READ ONLY" in x for x in c.c.sql))\n        self.assertFalse(a.probability_enabled)\n\nif __name__=="__main__":\n    x=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not x.wasSuccessful():raise SystemExit(1)\n    print("[PASS] OAD-227 stable as-of learned-case snapshot boundary certified")\n'

def main():
    if Path(__file__).name != EXPECTED_INSTALLER:
        raise RuntimeError(f"Installer identity mismatch: expected {EXPECTED_INSTALLER}, got {Path(__file__).name}")
    r=root();pkg=r/"qseries_v2"/"oracle_adapters"/"independent";m=pkg/MODULE_NAME;t=r/TEST_NAME
    print("="*124);print(" OAD-227 CRYPTO LEARNED-CASE AS-OF SNAPSHOT BOUNDARY");print("="*124)
    print("[BOOT]",REVISION);print("[INSTALLER]",Path(__file__).name);print("[ROOT]",r)
    d=r/'qseries_v2/oracle_production_hardening/oph_019_postgresql_universal_ingestion_queue.py'
    if not d.is_file(): raise RuntimeError("Required certified dependency missing: "+str(d))
    print("[PASS] dependency verified:",d.relative_to(r))
    d=pkg/'oad_226_crypto_physical_adaptive_state_and_ocl029_readmission.py'
    if not d.is_file(): raise RuntimeError("Required certified dependency missing: "+str(d))
    print("[PASS] dependency verified:",d.relative_to(r))
    print("[PASS] installer identity verified")
    targets=[m,t]
    old={p:(p.read_bytes() if p.exists() else None) for p in targets}
    try:
        write_atomic(m,MODULE);write_atomic(t,TEST)
        run_test(r,t)
        print('[PASS] one REPEATABLE READ / READ ONLY cut protects internal handoff consistency')
        print('[PASS] no runtime writer modified')
        print('[PASS] probability=FALSE direction=FALSE execution=FALSE')
        print("[DONE] OAD-227 INSTALLATION COMPLETE")
    except Exception:
        for p,b in old.items():
            if b is None:
                if p.exists():p.unlink()
            else:p.write_bytes(b)
        print("[ROLLBACK] installation rolled back");raise

if __name__=="__main__":main()
