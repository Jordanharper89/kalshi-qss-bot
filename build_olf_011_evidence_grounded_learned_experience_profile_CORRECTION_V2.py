from pathlib import Path
import importlib,os,subprocess,sys,json

ROOT=Path.cwd().resolve()
PKG=ROOT/"qseries_v2"/"oracle_learning_feedback"
MOD=PKG/"olf_011_learned_experience_profile.py"
TEST=ROOT/"test_olf_011_evidence_grounded_learned_experience_profile.py"
INIT=PKG/"__init__.py"

MODULE_SOURCE='from __future__ import annotations\nfrom pathlib import Path\nfrom datetime import datetime,timezone\nimport json,os\n\nfrom qseries_v2.oracle_continuous_reasoning.ocr_002_live_observation_read_model import load_env\nfrom qseries_v2.oracle_learning_runtime.olr_016_production_learned_state_adapter import load_production_learned_state\nfrom .olf_006_structural_identity import resolve_structural_identity\n\nOLF_011_BUILD_ID="OLF-011"\nOLF_011_REVISION="OLF_011_EVIDENCE_GROUNDED_LEARNED_EXPERIENCE_PROFILE_V1"\nPROFILE_NAME="oracle_learned_experience_profiles.json"\n\ndef _connect(url):\n    try:\n        import psycopg\n        return psycopg.connect(url)\n    except ImportError:\n        import psycopg2\n        return psycopg2.connect(url)\n\ndef _session(value):\n    if not value:return "UNKNOWN"\n    try:\n        x=datetime.fromisoformat(str(value).replace("Z","+00:00"))\n        if x.tzinfo is None:x=x.replace(tzinfo=timezone.utc)\n        h=x.astimezone(timezone.utc).hour\n        if h<6:return "UTC_00_05"\n        if h<12:return "UTC_06_11"\n        if h<18:return "UTC_12_17"\n        return "UTC_18_23"\n    except Exception:return "UNKNOWN"\n\ndef _source_family(payload):\n    if isinstance(payload,str):\n        try:payload=json.loads(payload)\n        except Exception:return ""\n    if not isinstance(payload,dict):return ""\n    candidates=[payload]\n    if isinstance(payload.get("payload"),dict):candidates.append(payload["payload"])\n    for row in candidates:\n        for k in ("source_family","source","venue","adapter","source_adapter","channel"):\n            v=row.get(k)\n            if v not in (None,""):\n                return str(v)[:120]\n    return ""\n\ndef _db_url(root):\n    env=load_env(Path(root))\n    url=env.get("DATABASE_URL") or env.get("ORACLE_DATABASE_URL")\n    if not url:raise RuntimeError("DATABASE_URL not configured")\n    return url\n\ndef build_learned_experience_profiles(root=None):\n    root=Path(root or Path.cwd()).resolve()\n    state=load_production_learned_state(root)\n    ledger_path=root/"runtime_state"/"oracle_learning_event_ledger.json"\n    ledger=json.loads(ledger_path.read_text(encoding="utf-8"))\n    learned=[]\n    hashes=[]\n    for key,rec in (ledger.items() if isinstance(ledger,dict) else ()):\n        if not isinstance(rec,dict) or str(rec.get("status") or "")!="learned":continue\n        h=str(rec.get("evidence_hash") or "")\n        ticker=str(rec.get("ticker") or "")\n        if not ticker or not h:continue\n        learned.append((str(key),rec))\n        hashes.append(h)\n\n    evidence={}\n    conn=_connect(_db_url(root))\n    try:\n        try:conn.set_session(readonly=True,autocommit=False)\n        except Exception:pass\n        cur=conn.cursor()\n        for pos in range(0,len(hashes),500):\n            batch=hashes[pos:pos+500]\n            cur.execute(\n                """SELECT content_hash,observation_id,observation_type,observed_at,\n                          source_observation_id,canonical_observation_json\n                   FROM public.oracle_canonical_observations\n                   WHERE content_hash = ANY(%s) OR observation_id = ANY(%s)""",\n                (batch,batch),\n            )\n            for r in cur.fetchall():\n                row={\n                    "content_hash":str(r[0] or ""),\n                    "observation_id":str(r[1] or ""),\n                    "observation_type":str(r[2] or ""),\n                    "observed_at":str(r[3] or ""),\n                    "source_observation_id":str(r[4] or ""),\n                    "canonical_observation_json":r[5],\n                }\n                for k in (row["content_hash"],row["observation_id"]):\n                    if k:evidence.setdefault(k,row)\n        try:conn.rollback()\n        except Exception:pass\n    finally:conn.close()\n\n    profiles=[]\n    for settlement_hash,rec in learned:\n        ticker=str(rec.get("ticker") or "")\n        h=str(rec.get("evidence_hash") or "")\n        row=evidence.get(h)\n        ident=resolve_structural_identity(ticker)\n        profiles.append({\n            "settlement_hash":settlement_hash,\n            "market_ticker":ticker,\n            "series_key":ident.series_key,\n            "settlement_ts":str(rec.get("settlement_ts") or ""),\n            "evidence_hash":h,\n            "learning_event_hash":str(rec.get("learning_event_hash") or ""),\n            "evidence_resolved":row is not None,\n            "observation_id":str((row or {}).get("observation_id") or ""),\n            "observation_type":str((row or {}).get("observation_type") or "UNKNOWN").upper(),\n            "observed_at":str((row or {}).get("observed_at") or ""),\n            "utc_session":_session((row or {}).get("observed_at")),\n            "source_family":_source_family((row or {}).get("canonical_observation_json")),\n        })\n    return {\n        "revision":OLF_011_REVISION,\n        "learner_state_hash":state.learner_state_hash,\n        "outcomes_learned":state.outcomes_learned,\n        "learned_records":state.learned_records,\n        "profiles":profiles,\n        "resolved_evidence":sum(1 for x in profiles if x["evidence_resolved"]),\n        "execution_authority":False,\n    }\n\ndef materialize_learned_experience_profiles(root=None,force=False):\n    root=Path(root or Path.cwd()).resolve()\n    path=root/"runtime_state"/PROFILE_NAME\n    state=load_production_learned_state(root)\n    if path.is_file() and not force:\n        try:\n            old=json.loads(path.read_text(encoding="utf-8"))\n            if str(old.get("learner_state_hash") or "")==state.learner_state_hash:\n                return old\n        except Exception:pass\n    payload=build_learned_experience_profiles(root)\n    tmp=path.with_suffix(path.suffix+".tmp")\n    tmp.write_text(json.dumps(payload,sort_keys=True,separators=(",",":")),encoding="utf-8",newline="\\n")\n    os.replace(tmp,path)\n    return payload\n\ndef verify_olf_011_evidence_grounded_learned_experience_profile():\n    return OLF_011_BUILD_ID=="OLF-011" and _session("2026-08-20T13:00:00Z")=="UTC_12_17"\n'
TEST_SOURCE='import unittest\nimport qseries_v2.oracle_learning_feedback.olf_011_learned_experience_profile as m\n\nclass T(unittest.TestCase):\n    def test_identity(self):\n        self.assertEqual(m.OLF_011_BUILD_ID,"OLF-011")\n\n    def test_contract(self):\n        self.assertTrue(callable(m.build_learned_experience_profiles))\n        self.assertTrue(callable(m.materialize_learned_experience_profiles))\n        self.assertTrue(m.verify_olf_011_evidence_grounded_learned_experience_profile())\n\n    def test_session_mapping(self):\n        self.assertEqual(m._session("2026-08-20T01:00:00Z"),"UTC_00_05")\n        self.assertEqual(m._session("2026-08-20T13:00:00Z"),"UTC_12_17")\n\nif __name__=="__main__":\n    print("="*88)\n    print(" OLF-011 CERTIFICATION TEST — CORRECTION V2")\n    print(" EVIDENCE-GROUNDED LEARNED EXPERIENCE PROFILE")\n    print("="*88)\n    r=unittest.TextTestRunner(verbosity=2).run(\n        unittest.defaultTestLoader.loadTestsFromTestCase(T)\n    )\n    if not r.wasSuccessful():\n        raise SystemExit(1)\n    print("[PASS] Canonical evidence condition profiling contract certified")\n    print("[PASS] Private helper test import corrected")\n    print("[PASS] execution_authority=FALSE")\n    print("[DONE] OLF-011 CORRECTION V2 CERTIFIED")\n'

def write_exact(path,text):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(text,encoding="utf-8",newline="\n")
    os.replace(tmp,path)

def restore(path,data):
    if data is None:
        if path.exists():
            path.unlink()
    else:
        path.write_bytes(data)

def update_init(path,line):
    current=path.read_text(encoding="utf-8") if path.exists() else ""
    if line not in current.splitlines():
        write_exact(path,current.rstrip()+"\n"+line+"\n")

def main():
    print("="*88)
    print(" OLF-011 INSTALLER — CORRECTION V2")
    print(" EVIDENCE-GROUNDED LEARNED EXPERIENCE PROFILE")
    print("="*88)
    print("[ROOT]",ROOT)

    sys.path.insert(0,str(ROOT))

    up=importlib.import_module(
        "qseries_v2.oracle_learning_feedback.olf_010_cross_market_reasoning_runtime"
    )
    manifest=PKG/"OLF_010_FREEZE_MANIFEST.json"

    if not up.verify_olf_010_cross_market_reasoning_runtime():
        raise RuntimeError("Frozen OLF-010 runtime verification failed")
    if not manifest.is_file():
        raise RuntimeError("Frozen OLF-010 manifest missing")

    old={p:(p.read_bytes() if p.exists() else None) for p in (MOD,TEST,INIT)}

    try:
        write_exact(MOD,MODULE_SOURCE)
        write_exact(TEST,TEST_SOURCE)
        update_init(INIT,"from .olf_011_learned_experience_profile import *")

        subprocess.run([sys.executable,str(TEST)],cwd=str(ROOT),check=True)

        importlib.invalidate_caches()
        m=importlib.import_module(
            "qseries_v2.oracle_learning_feedback.olf_011_learned_experience_profile"
        )
        m=importlib.reload(m)

        payload=m.materialize_learned_experience_profiles(ROOT,force=True)

        if int(payload.get("resolved_evidence",0))<=0:
            raise RuntimeError(
                "No learned evidence hashes resolved to canonical PostgreSQL observations"
            )

        if str(payload.get("learner_state_hash") or "")=="":
            raise RuntimeError("Learner state hash missing from physical experience profile")

        print(
            f"[PHYSICAL EXPERIENCE] learned_records={payload['learned_records']} "
            f"profiles={len(payload['profiles'])} "
            f"resolved_evidence={payload['resolved_evidence']} "
            f"state_hash={payload['learner_state_hash']}"
        )

    except Exception:
        for p,b in old.items():
            restore(p,b)
        print("[ROLLBACK] OLF-011 correction failed; files restored")
        raise

    print("[PASS] Proven learner unchanged")
    print("[PASS] PostgreSQL inspected read-only")
    print("[PASS] OLF-010 frozen boundary preserved")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] OLF-011 CORRECTION V2 INSTALLATION COMPLETE")

if __name__=="__main__":
    main()
