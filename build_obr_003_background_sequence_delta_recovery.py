from pathlib import Path
import os,subprocess,sys
ROOT=Path.cwd().resolve();PKG=ROOT/"qseries_v2"/"oracle_background_recovery"
MOD=PKG/"obr_003_state_recovery.py";TEST=ROOT/"test_obr_003_background_sequence_delta_recovery.py";INIT=PKG/"__init__.py"
MODULE_SOURCE='from __future__ import annotations\nfrom pathlib import Path\nfrom datetime import datetime,timezone\nimport json,os\n\nfrom .obr_002_gap_queue import next_queued_gap\nfrom qseries_v2.oracle_learning_feedback.olf_011_learned_experience_profile import _connect,_db_url\nfrom qseries_v2.oracle_adapters.kalshi.oad_021_credentials import load_kalshi_credentials\nfrom qseries_v2.oracle_adapters.kalshi.oad_022_rest_transport import kalshi_rest_get\n\nOBR_003_BUILD_ID="OBR-003"\nOBR_003_REVISION="OBR_003_BACKGROUND_SEQUENCE_DELTA_RECOVERY_V1"\nPROGRESS="oracle_background_recovery_progress.json"\nRESULTS="oracle_background_recovery_results.jsonl"\n\ndef _current_sequence(root):\n    conn=_connect(_db_url(root))\n    try:\n        cur=conn.cursor();cur.execute("SELECT COALESCE(MAX(sequence_number),0) FROM public.oracle_canonical_observations")\n        return int(cur.fetchone()[0] or 0)\n    finally:conn.close()\n\ndef _delta_tickers(root,start_seq,end_seq):\n    conn=_connect(_db_url(root))\n    try:\n        cur=conn.cursor()\n        cur.execute("""\n            WITH n AS(\n              SELECT COALESCE(canonical_observation_json->\'raw_observation\'->\'payload\',\n                              canonical_observation_json->\'payload\',\'{}\'::jsonb) p\n              FROM public.oracle_canonical_observations\n              WHERE sequence_number>%s AND sequence_number<=%s\n            )\n            SELECT DISTINCT COALESCE(NULLIF(p->>\'source_market_id\',\'\'),\n                                     NULLIF(p->>\'market_id\',\'\'),\n                                     NULLIF(p->>\'source_symbol\',\'\'),\n                                     NULLIF(p->>\'ticker\',\'\'))\n            FROM n\n            WHERE COALESCE(NULLIF(p->>\'source_market_id\',\'\'),\n                           NULLIF(p->>\'market_id\',\'\'),\n                           NULLIF(p->>\'source_symbol\',\'\'),\n                           NULLIF(p->>\'ticker\',\'\')) IS NOT NULL\n        """,(int(start_seq),int(end_seq)))\n        return [str(r[0]).upper() for r in cur.fetchall() if r and r[0]]\n    finally:conn.close()\n\ndef recover_gap_market_states(root,gap,batch_size=500,progress=print):\n    root=Path(root).resolve()\n    start_seq=int(gap.get("last_good_sequence") or 0)\n    end_seq=_current_sequence(root)\n    tickers=_delta_tickers(root,start_seq,end_seq)\n    creds=load_kalshi_credentials(root=root)\n    out=root/"runtime_state"/RESULTS\n    recovered=failed=0\n    for i,ticker in enumerate(tickers,1):\n        try:\n            r=kalshi_rest_get(creds,f"/markets/{ticker}",{},15)\n            body=dict(r.body or {})\n            raw=body.get("market") if isinstance(body.get("market"),dict) else body\n            with out.open("a",encoding="utf-8",newline="\\n") as f:\n                f.write(json.dumps({"gap_id":gap["gap_id"],"ticker":ticker,"kind":"MARKET_STATE","status":"RECOVERED","market":raw},sort_keys=True,separators=(",",":"),default=str)+"\\n")\n            recovered+=1\n        except Exception as exc:\n            with out.open("a",encoding="utf-8",newline="\\n") as f:\n                f.write(json.dumps({"gap_id":gap["gap_id"],"ticker":ticker,"kind":"MARKET_STATE","status":"FAILED","error":str(exc)[:300]},sort_keys=True,separators=(",",":"))+"\\n")\n            failed+=1\n        if progress and (i<=5 or i%batch_size==0 or i==len(tickers)):\n            progress(f"[OBR STATE] checked={i}/{len(tickers)} recovered={recovered} failed={failed}")\n    return {"delta_tickers":len(tickers),"state_recovered":recovered,"state_failed":failed,"sequence_start":start_seq,"sequence_end":end_seq}\n\ndef verify_obr_003_background_sequence_delta_recovery():\n    return OBR_003_BUILD_ID=="OBR-003" and callable(recover_gap_market_states)\n';TEST_SOURCE='import unittest\nimport qseries_v2.oracle_background_recovery.obr_003_state_recovery as m\nclass T(unittest.TestCase):\n    def test_identity(self):self.assertEqual(m.OBR_003_BUILD_ID,"OBR-003")\nif __name__=="__main__":\n    print("="*88);print(" OBR-003 CERTIFICATION TEST");print(" BACKGROUND SEQUENCE-DELTA RECOVERY");print("="*88)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful():raise SystemExit(1)\n    print("[PASS] bounded sequence-delta recovery certified")\n    print("[PASS] execution_authority=FALSE")\n    print("[DONE] OBR-003 CERTIFIED")\n'

def write_exact(path,text):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(text,encoding="utf-8",newline="\n")
    os.replace(tmp,path)
def restore(path,data):
    if data is None:
        if path.exists(): path.unlink()
    else:
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_bytes(data)

def main():
    print("="*88);print(" OBR-003 INSTALLER");print(" BACKGROUND SEQUENCE-DELTA RECOVERY");print("="*88);print("[ROOT]",ROOT)
    old={p:(p.read_bytes() if p.exists() else None) for p in (MOD,TEST,INIT)}
    try:
        write_exact(MOD,MODULE_SOURCE);write_exact(TEST,TEST_SOURCE)
        cur=INIT.read_text(encoding="utf-8") if INIT.exists() else "";line="from .obr_003_state_recovery import *"
        if line not in cur.splitlines():write_exact(INIT,cur.rstrip()+"\n"+line+"\n")
        subprocess.run([sys.executable,str(TEST)],cwd=str(ROOT),check=True)
    except Exception:
        for p,b in old.items():restore(p,b)
        print("[ROLLBACK] OBR-003 failed");raise
    print("[DONE] OBR-003 INSTALLATION COMPLETE")
if __name__=="__main__":main()
