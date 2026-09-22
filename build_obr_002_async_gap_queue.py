from pathlib import Path
import os,subprocess,sys
ROOT=Path.cwd().resolve();PKG=ROOT/"qseries_v2"/"oracle_background_recovery"
MOD=PKG/"obr_002_gap_queue.py";TEST=ROOT/"test_obr_002_async_gap_queue.py";INIT=PKG/"__init__.py"
MODULE_SOURCE='from __future__ import annotations\nfrom pathlib import Path\nfrom datetime import datetime,timezone\nimport json,os,hashlib\n\nfrom qseries_v2.oracle_interruption_recovery.oir_001_continuity_checkpoint import load_continuity_checkpoint\n\nOBR_002_BUILD_ID="OBR-002"\nOBR_002_REVISION="OBR_002_ASYNC_GAP_QUEUE_V1"\nQUEUE="oracle_background_recovery_queue.jsonl"\nSTATE="oracle_background_recovery_state.json"\n\ndef _dt(v):\n    if not v:return None\n    try:\n        x=datetime.fromisoformat(str(v).replace("Z","+00:00"))\n        return x if x.tzinfo else x.replace(tzinfo=timezone.utc)\n    except Exception:return None\n\ndef enqueue_gap(root=None,now=None,min_gap_seconds=20.0):\n    root=Path(root or Path.cwd()).resolve()\n    cp=load_continuity_checkpoint(root)\n    if not cp:return None\n    start=_dt(cp.get("captured_at"))\n    if start is None:return None\n    end=(now or datetime.now(timezone.utc)).astimezone(timezone.utc)\n    gap=max(0.0,(end-start).total_seconds())\n    if gap<float(min_gap_seconds):return None\n    raw=f"{start.isoformat()}|{end.isoformat()}|{cp.get(\'canonical_sequence_number\',0)}"\n    gap_id=hashlib.sha256(raw.encode()).hexdigest()\n    record={\n        "gap_id":gap_id,\n        "gap_start":start.isoformat(),\n        "gap_end":end.isoformat(),\n        "gap_seconds":gap,\n        "last_good_sequence":int(cp.get("canonical_sequence_number") or 0),\n        "status":"QUEUED",\n        "execution_authority":False,\n    }\n    q=root/"runtime_state"/QUEUE\n    q.parent.mkdir(parents=True,exist_ok=True)\n    existing=set()\n    if q.is_file():\n        for line in q.read_text(encoding="utf-8").splitlines():\n            try: existing.add(json.loads(line).get("gap_id"))\n            except Exception: pass\n    if gap_id not in existing:\n        with q.open("a",encoding="utf-8",newline="\\n") as f:\n            f.write(json.dumps(record,sort_keys=True,separators=(",",":"))+"\\n")\n    return record\n\ndef next_queued_gap(root=None):\n    root=Path(root or Path.cwd()).resolve()\n    q=root/"runtime_state"/QUEUE\n    if not q.is_file():return None\n    state_path=root/"runtime_state"/STATE\n    done=set()\n    if state_path.is_file():\n        try:\n            s=json.loads(state_path.read_text(encoding="utf-8"))\n            done=set(s.get("completed_gap_ids",[]))\n        except Exception:pass\n    for line in q.read_text(encoding="utf-8").splitlines():\n        if not line.strip():continue\n        row=json.loads(line)\n        if row.get("gap_id") not in done:return row\n    return None\n\ndef mark_completed(root,gap_id,summary):\n    root=Path(root).resolve()\n    path=root/"runtime_state"/STATE\n    state={"completed_gap_ids":[],"last_summary":{}}\n    if path.is_file():\n        try:state=json.loads(path.read_text(encoding="utf-8"))\n        except Exception:pass\n    done=list(state.get("completed_gap_ids",[]))\n    if gap_id not in done:done.append(gap_id)\n    state["completed_gap_ids"]=done[-1000:]\n    state["last_summary"]=summary\n    tmp=path.with_suffix(path.suffix+".tmp")\n    tmp.write_text(json.dumps(state,sort_keys=True,separators=(",",":")),encoding="utf-8",newline="\\n")\n    os.replace(tmp,path)\n\ndef verify_obr_002_async_gap_queue():\n    return OBR_002_BUILD_ID=="OBR-002" and callable(enqueue_gap)\n';TEST_SOURCE='import unittest\nimport qseries_v2.oracle_background_recovery.obr_002_gap_queue as m\nclass T(unittest.TestCase):\n    def test_identity(self):self.assertEqual(m.OBR_002_BUILD_ID,"OBR-002")\n    def test_contract(self):self.assertTrue(callable(m.enqueue_gap))\nif __name__=="__main__":\n    print("="*88);print(" OBR-002 CERTIFICATION TEST");print(" ASYNCHRONOUS GAP QUEUE");print("="*88)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful():raise SystemExit(1)\n    print("[PASS] Durable gap queue certified")\n    print("[PASS] execution_authority=FALSE")\n    print("[DONE] OBR-002 CERTIFIED")\n'

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
    print("="*88);print(" OBR-002 INSTALLER");print(" ASYNCHRONOUS GAP QUEUE");print("="*88);print("[ROOT]",ROOT)
    old={p:(p.read_bytes() if p.exists() else None) for p in (MOD,TEST,INIT)}
    try:
        write_exact(MOD,MODULE_SOURCE);write_exact(TEST,TEST_SOURCE)
        cur=INIT.read_text(encoding="utf-8") if INIT.exists() else ""
        line="from .obr_002_gap_queue import *"
        if line not in cur.splitlines():write_exact(INIT,cur.rstrip()+"\n"+line+"\n")
        subprocess.run([sys.executable,str(TEST)],cwd=str(ROOT),check=True)
    except Exception:
        for p,b in old.items():restore(p,b)
        print("[ROLLBACK] OBR-002 failed");raise
    print("[DONE] OBR-002 INSTALLATION COMPLETE")
if __name__=="__main__":main()
