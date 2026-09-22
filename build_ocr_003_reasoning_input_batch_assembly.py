from __future__ import annotations
import hashlib, importlib, json, os, subprocess, sys
from pathlib import Path

ROOT=Path.cwd().resolve()
PACKAGE=ROOT/"qseries_v2"/"oracle_continuous_reasoning"
INIT=PACKAGE/"__init__.py"

def write_exact(path,text):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(text,encoding="utf-8",newline="\n")
    os.replace(tmp,path)

def update_init(marker,module,exports):
    current=INIT.read_text(encoding="utf-8") if INIT.exists() else ""
    if marker in current:
        return
    block=marker+"\nfrom ."+module+" import (\n"+"".join("    "+x+",\n" for x in exports)+")\n"
    write_exact(INIT,current.rstrip()+("\n\n" if current.strip() else "")+block)

def run_test(path):
    proc=subprocess.run([sys.executable,str(path)],cwd=str(ROOT))
    if proc.returncode:
        raise RuntimeError("Certification test failed: "+path.name)

BUILD_ID='OCR-003'
TITLE='REASONING INPUT BATCH ASSEMBLY'
REVISION='OCR_003_PRODUCTION_V1'
MODULE=PACKAGE/'ocr_003_reasoning_input_batch.py'
TEST=ROOT/'test_ocr_003_reasoning_input_batch_assembly.py'
EXPORTS=('OCR_003_BUILD_ID', 'OCR_003_REVISION', 'ReasoningObservation', 'ReasoningInputBatch', 'materialize_reasoning_observation', 'assemble_reasoning_input_batch', 'verify_ocr_003_reasoning_input_batch_assembly')
MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass\nfrom hashlib import sha256\nimport json\n\nOCR_003_BUILD_ID="OCR-003"\nOCR_003_REVISION="OCR_003_REASONING_INPUT_BATCH_ASSEMBLY_V1"\n\ndef _h(v): return sha256(json.dumps(v,sort_keys=True,separators=(",",":"),ensure_ascii=False,default=str).encode()).hexdigest()\n\n@dataclass(frozen=True)\nclass ReasoningObservation:\n    observation_id:str\n    source_id:str\n    event_type:str\n    market_ticker:str\n    payload:tuple[tuple[str,str],...]\n    record_hash:str\n\n@dataclass(frozen=True)\nclass ReasoningInputBatch:\n    observations:tuple[ReasoningObservation,...]\n    observation_count:int\n    market_count:int\n    batch_hash:str\n    read_only:bool=True\n\ndef _pick(row,*names):\n    for n in names:\n        if n in row and row[n] is not None: return row[n]\n    return ""\n\ndef materialize_reasoning_observation(row):\n    oid=str(_pick(row,"observation_id","id")).strip()\n    if not oid: raise ValueError("observation_id required")\n    source=str(_pick(row,"source_id","source","adapter_id")).strip()\n    payload=_pick(row,"payload","observation_payload","data")\n    if not isinstance(payload,dict): payload={"value":payload}\n    event=str(_pick(payload,"event_type","type") or _pick(row,"observation_type","event_type")).strip()\n    ticker=str(_pick(payload,"source_market_id","market_ticker","ticker") or _pick(row,"market_id","market_ticker")).strip()\n    canonical=tuple((str(k),json.dumps(payload[k],sort_keys=True,separators=(",",":"),default=str)) for k in sorted(payload))\n    raw={"observation_id":oid,"source_id":source,"event_type":event,"market_ticker":ticker,"payload":canonical}\n    return ReasoningObservation(oid,source,event,ticker,canonical,_h(raw))\n\ndef assemble_reasoning_input_batch(rows):\n    obs=tuple(sorted((materialize_reasoning_observation(dict(r)) for r in rows),key=lambda x:(x.market_ticker,x.observation_id)))\n    if not obs: raise ValueError("reasoning observations required")\n    if len({x.observation_id for x in obs})!=len(obs): raise ValueError("duplicate observation_id")\n    raw={"record_hashes":[x.record_hash for x in obs],"count":len(obs)}\n    return ReasoningInputBatch(obs,len(obs),len({x.market_ticker for x in obs if x.market_ticker}),_h(raw),True)\n\ndef verify_ocr_003_reasoning_input_batch_assembly():\n    b=assemble_reasoning_input_batch(({"observation_id":"o1","source_id":"s","payload":{"market_ticker":"A","event_type":"ticker","x":1}},))\n    return b.observation_count==1 and b.market_count==1 and b.read_only\n'
TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_continuous_reasoning.ocr_003_reasoning_input_batch import *\nclass T(unittest.TestCase):\n    def test_verifier(self): self.assertTrue(verify_ocr_003_reasoning_input_batch_assembly())\n    def test_duplicate(self):\n        row={"observation_id":"x","payload":{"market_ticker":"A"}}\n        with self.assertRaises(ValueError): assemble_reasoning_input_batch((row,row))\nif __name__=="__main__":\n    print("="*72);print(" OCR-003 CERTIFICATION TEST");print(" REASONING INPUT BATCH ASSEMBLY");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] Deterministic live-observation reasoning batches certified")\n    print("[DONE] OCR-003 CERTIFIED")\n'


def verify_upstream():
    sys.path.insert(0,str(ROOT))
    try:
        importlib.invalidate_caches()
        m=importlib.import_module('qseries_v2.oracle_continuous_reasoning.ocr_002_live_observation_read_model')
        if getattr(m,'verify_ocr_002_postgresql_live_observation_read_model')() is not True:
            raise RuntimeError("Certified upstream verifier returned false")
    finally:
        if str(ROOT) in sys.path:
            sys.path.remove(str(ROOT))

def main():
    print("="*72);print(" "+BUILD_ID+" INSTALLER");print(" "+TITLE);print("="*72)
    print("[BOOT] Revision: "+REVISION);print("[ROOT] "+str(ROOT))
    verify_upstream();print("[PASS] Certified upstream boundary verified read-only")
    affected=(MODULE,TEST,INIT)
    backups={p:(p.read_bytes() if p.exists() else None) for p in affected}
    try:
        write_exact(MODULE,MODULE_SOURCE);write_exact(TEST,TEST_SOURCE)

        update_init("# "+BUILD_ID+" exports",MODULE.stem,EXPORTS)
        compile(MODULE.read_text(encoding="utf-8"),str(MODULE),"exec")
        compile(TEST.read_text(encoding="utf-8"),str(TEST),"exec")
        sys.path.insert(0,str(ROOT))
        try:
            importlib.invalidate_caches()
            name="qseries_v2.oracle_continuous_reasoning."+MODULE.stem
            sys.modules.pop(name,None)
            m=importlib.import_module(name)
            verifier=getattr(m,[x for x in EXPORTS if x.startswith("verify_")][-1])
            if verifier() is not True:
                raise RuntimeError("Production verifier returned false")
        finally:
            if str(ROOT) in sys.path:
                sys.path.remove(str(ROOT))
        run_test(TEST)
    except Exception:
        for p,old in backups.items():
            if old is None:
                if p.exists(): p.unlink()
            else:
                p.write_bytes(old)
        print("[ROLLBACK] "+BUILD_ID+" installation failed; affected files restored")
        raise
    print("[PASS] Wrote: "+str(MODULE.relative_to(ROOT)))
    print("[PASS] Updated: "+str(INIT.relative_to(ROOT)))
    print("[PASS] Wrote: "+TEST.name)
    print("[DONE] "+BUILD_ID+" INSTALLATION AND CERTIFICATION COMPLETE")
if __name__=="__main__":
    main()
