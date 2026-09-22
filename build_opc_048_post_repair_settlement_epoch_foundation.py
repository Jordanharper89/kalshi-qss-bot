from pathlib import Path
import ast, importlib, os, subprocess, sys
ROOT=Path.cwd().resolve()
TARGET=ROOT/'qseries_v2/oracle_pre_settlement_coverage/opc_048_post_repair_settlement_epoch_foundation.py'
TEST=ROOT/'test_opc_048_post_repair_settlement_epoch_foundation.py'
SOURCE='from pathlib import Path\nfrom datetime import datetime, timezone\nimport json, hashlib\n\nOPC_048_BUILD_ID="OPC-048"\nOPC_048_REVISION="OPC_048_POST_REPAIR_SETTLEMENT_EPOCH_FOUNDATION"\nEPOCH_FILE="OPC_048_POST_REPAIR_SETTLEMENT_EPOCH.json"\n\ndef _utcnow():\n    return datetime.now(timezone.utc)\n\ndef epoch_path(root=None):\n    return Path(root or Path.cwd()).resolve()/EPOCH_FILE\n\ndef establish_epoch(root=None):\n    p=epoch_path(root)\n    if p.exists():\n        data=json.loads(p.read_text(encoding="utf-8"))\n        return {**data,"created":False}\n    ts=_utcnow().isoformat().replace("+00:00","Z")\n    payload={"build_id":OPC_048_BUILD_ID,"repair_epoch":ts,"purpose":"post-repair settlement evidence boundary","read_only":True,"probability_enabled":False,"execution_authority":False}\n    payload["epoch_hash"]=hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(",",":")).encode()).hexdigest()\n    p.write_text(json.dumps(payload,sort_keys=True,indent=2)+"\\n",encoding="utf-8")\n    return {**payload,"created":True}\n\ndef load_epoch(root=None):\n    p=epoch_path(root)\n    if not p.exists(): raise RuntimeError("OPC-048 repair epoch not established")\n    return json.loads(p.read_text(encoding="utf-8"))\n\ndef verify_opc_048():\n    return OPC_048_BUILD_ID=="OPC-048"\n'
TEST_SOURCE='import unittest\nfrom pathlib import Path\nfrom qseries_v2.oracle_pre_settlement_coverage import opc_048_post_repair_settlement_epoch_foundation as m\nclass T(unittest.TestCase):\n def test_epoch(self):\n  self.assertTrue(m.verify_opc_048());x=m.establish_epoch();self.assertIn("repair_epoch",x);self.assertTrue(m.epoch_path().exists());self.assertTrue(x["read_only"]);self.assertFalse(x["probability_enabled"]);self.assertFalse(x["execution_authority"]);print("[EPOCH]",x)\nif __name__=="__main__":unittest.main(verbosity=2)\n'

def atomic_write(path,text):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_name(path.name+f".{os.getpid()}.tmp")
    tmp.write_text(text,encoding="utf-8",newline="\n")
    os.replace(tmp,path)

def restore(path,before):
    if before is None:
        if path.exists(): path.unlink()
    else:
        path.write_bytes(before)

def main():
    print("="*88)
    print(' OPC-048 INSTALLER — POST-REPAIR SETTLEMENT EPOCH FOUNDATION')
    print("="*88)
    print("[ROOT]",ROOT)
    before_m=TARGET.read_bytes() if TARGET.exists() else None
    before_t=TEST.read_bytes() if TEST.exists() else None
    try:
        ast.parse(SOURCE); ast.parse(TEST_SOURCE)
        print("[PASS] payload syntax verified")
        atomic_write(TARGET,SOURCE); atomic_write(TEST,TEST_SOURCE)
        importlib.invalidate_caches()
        subprocess.run([sys.executable,str(TEST)],cwd=str(ROOT),check=True,timeout=90)
    except Exception:
        restore(TARGET,before_m); restore(TEST,before_t)
        print("[ROLLBACK] installation failed; affected files restored")
        raise
    print("[DONE] INSTALLATION COMPLETE")

if __name__=="__main__":
    main()
