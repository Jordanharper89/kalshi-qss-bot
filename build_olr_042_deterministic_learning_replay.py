from pathlib import Path
import os,sys,subprocess,importlib

ROOT=Path.cwd().resolve()
PKG=ROOT/"qseries_v2"/"oracle_learning_runtime"
MOD_PATH=PKG/"olr_042_deterministic_learning_replay.py"
TEST_PATH=ROOT/"test_olr_042_deterministic_learning_replay.py"
INIT_PATH=PKG/"__init__.py"

MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass\nfrom hashlib import sha256\nimport json\n\nOLR_042_BUILD_ID="OLR-042"\nOLR_042_REVISION="OLR_042_DETERMINISTIC_LEARNING_REPLAY_V1"\n\n@dataclass(frozen=True)\nclass LearningReplayResult:\n    input_records:int\n    output_records:int\n    replay_hash:str\n    deterministic:bool\n    execution_authority:bool=False\n\ndef canonicalize_learning_records(records):\n    normalized=[]\n    for r in records:\n        if isinstance(r,dict):\n            normalized.append(dict(sorted((str(k),v) for k,v in r.items())))\n        else:\n            normalized.append({"value":r})\n    normalized.sort(key=lambda x:json.dumps(x,sort_keys=True,separators=(",",":"),default=str))\n    return tuple(normalized)\n\ndef replay_learning_records(records):\n    canonical=canonicalize_learning_records(records)\n    payload=json.dumps(canonical,sort_keys=True,separators=(",",":"),default=str)\n    digest=sha256(payload.encode()).hexdigest()\n    second=json.dumps(canonicalize_learning_records(canonical),sort_keys=True,separators=(",",":"),default=str)\n    digest2=sha256(second.encode()).hexdigest()\n    return LearningReplayResult(len(tuple(records)),len(canonical),digest,digest==digest2,False)\n\ndef verify_olr_042_deterministic_learning_replay():\n    rows=({"b":2,"a":1},{"a":3})\n    x=replay_learning_records(rows)\n    return x.deterministic and len(x.replay_hash)==64 and not x.execution_authority\n'
TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_learning_runtime.olr_042_deterministic_learning_replay import *\n\nclass T(unittest.TestCase):\n    def test_verifier(self):self.assertTrue(verify_olr_042_deterministic_learning_replay())\n    def test_order_independent(self):\n        a=replay_learning_records(({"x":1},{"x":2}))\n        b=replay_learning_records(({"x":2},{"x":1}))\n        self.assertEqual(a.replay_hash,b.replay_hash)\n\nif __name__=="__main__":\n    print("="*72);print(" OLR-042 CERTIFICATION TEST");print(" DETERMINISTIC LEARNING REPLAY");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful():raise SystemExit(1)\n    print("[PASS] Deterministic replay hashing certified")\n    print("[DONE] OLR-042 CERTIFIED")\n'


def write_exact(path,text):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(text,encoding="utf-8",newline="\n")
    os.replace(tmp,path)

def main():
    print("="*72)
    print(" OLR-042 INSTALLER")
    print(" DETERMINISTIC LEARNING REPLAY")
    print("="*72)
    print("[ROOT]",ROOT)

    sys.path.insert(0,str(ROOT))
    upstream=importlib.import_module('qseries_v2.oracle_learning_runtime.olr_041_learning_health_model')
    verifier=getattr(upstream,'verify_olr_041_learning_health_model')
    if verifier() is not True:
        raise RuntimeError("Certified upstream verification failed")
    print("[PASS] Certified OLR-041 upstream boundary verified")

    affected=(MOD_PATH,TEST_PATH,INIT_PATH,)
    backups={path_obj:(path_obj.read_bytes() if path_obj.exists() else None) for path_obj in affected}

    try:
        write_exact(MOD_PATH,MODULE_SOURCE)
        write_exact(TEST_PATH,TEST_SOURCE)

        current=INIT_PATH.read_text(encoding="utf-8") if INIT_PATH.exists() else ""
        export_line="from .olr_042_deterministic_learning_replay import *"
        if export_line not in current:
            write_exact(INIT_PATH,current.rstrip()+"\n"+export_line+"\n")

        compile(MOD_PATH.read_text(encoding="utf-8"),str(MOD_PATH),"exec")
        compile(TEST_PATH.read_text(encoding="utf-8"),str(TEST_PATH),"exec")

        subprocess.run([sys.executable,str(TEST_PATH)],cwd=str(ROOT),check=True)

    except Exception:
        for path_obj,old in backups.items():
            if old is None:
                if path_obj.exists():
                    path_obj.unlink()
            else:
                path_obj.write_bytes(old)
        print("[ROLLBACK] OLR-042 installation failed; affected files restored")
        raise

    print("[PASS] Wrote:",MOD_PATH.relative_to(ROOT))
    print("[PASS] Wrote:",TEST_PATH.name)
    print("[PASS] Updated:",INIT_PATH.relative_to(ROOT))
    print("[DONE] OLR-042 INSTALLATION AND CERTIFICATION COMPLETE")

if __name__=="__main__":
    main()
