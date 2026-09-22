from __future__ import annotations
import hashlib, importlib, json, os, subprocess, sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent

def locate_repository():
    candidates=[]
    for base in (Path.cwd().resolve(), SCRIPT_DIR):
        candidates += [base, base/"kalshi-qss-bot"]
        for p in base.parents:
            candidates += [p, p/"kalshi-qss-bot"]
    seen=set()
    for c in candidates:
        try: c=c.resolve()
        except OSError: continue
        if c in seen: continue
        seen.add(c)
        if (c/"qseries_v2").is_dir():
            return c
    raise SystemExit("[ERROR] Could not locate current Q Series repository.")

ROOT=locate_repository()
PACKAGE=ROOT/"qseries_v2"/"oracle_adapters"/"kalshi"
INIT=PACKAGE/"__init__.py"

def write_exact(path,text):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(text.lstrip("\n"),encoding="utf-8",newline="\n")
    os.replace(tmp,path)

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()

def update_init(marker,module,exports):
    current=INIT.read_text(encoding="utf-8") if INIT.exists() else ""
    if marker in current: return
    block=marker+"\nfrom ."+module+" import (\n"+"".join("    "+x+",\n" for x in exports)+")\n"
    write_exact(INIT,current.rstrip()+("\n\n" if current.strip() else "")+block)

def run_test(path):
    p=subprocess.run([sys.executable,str(path)],cwd=str(ROOT))
    if p.returncode:
        raise RuntimeError("Certification test failed: "+path.name)

BUILD_ID='OAD-014'
TITLE='KALSHI SEQUENCE INTEGRITY + GAP DETECTION + RESYNC'
REVISION='OAD_014_PRODUCTION_V1'
MODULE=PACKAGE/'oad_014_sequence_integrity.py'
TEST=ROOT/'test_oad_014_kalshi_sequence_integrity_gap_detection_resync.py'
EXPORTS=('OAD_014_BUILD_ID', 'OAD_014_REVISION', 'SequenceIntegrityDecision', 'evaluate_sequence_integrity', 'build_orderbook_resync_command', 'build_oad_014_certification_manifest', 'verify_oad_014_kalshi_sequence_integrity_gap_detection_resync')
MODULE_SOURCE=r"""
from dataclasses import dataclass
from types import MappingProxyType

OAD_014_BUILD_ID="OAD-014"
OAD_014_REVISION="OAD_014_KALSHI_SEQUENCE_INTEGRITY_GAP_DETECTION_RESYNC_V1"

@dataclass(frozen=True)
class SequenceIntegrityDecision:
    sid:int
    previous_seq:int|None
    current_seq:int
    status:str
    accept:bool
    resync_required:bool
    reason:str

def evaluate_sequence_integrity(sid,previous_seq,current_seq,event_type):
    sid=int(sid); cur=int(current_seq)
    if sid<0 or cur<0: raise ValueError("non-negative sid/sequence required")
    if event_type=="orderbook_snapshot":
        return SequenceIntegrityDecision(sid,previous_seq,cur,"SNAPSHOT_BASELINE",True,False,"snapshot")
    if previous_seq is None:
        return SequenceIntegrityDecision(sid,None,cur,"NO_BASELINE",False,True,"missing_snapshot_or_baseline")
    prev=int(previous_seq)
    if cur==prev+1:
        return SequenceIntegrityDecision(sid,prev,cur,"IN_ORDER",True,False,"contiguous")
    if cur<=prev:
        return SequenceIntegrityDecision(sid,prev,cur,"STALE_OR_DUPLICATE",False,False,"non_advancing_sequence")
    return SequenceIntegrityDecision(sid,prev,cur,"GAP",False,True,"sequence_gap")

def build_orderbook_resync_command(command_id,sid,market_tickers):
    tickers=tuple(market_tickers)
    if int(command_id)<1 or int(sid)<0 or not tickers:
        raise ValueError("valid command id, sid, market_tickers required")
    return {"id":int(command_id),"cmd":"update_subscription",
            "params":{"sid":int(sid),"market_tickers":list(tickers),"action":"get_snapshot"}}

def build_oad_014_certification_manifest():
    return MappingProxyType({"build_id":OAD_014_BUILD_ID,"revision":OAD_014_REVISION,
        "sequence_gap_detection":True,"snapshot_resync_action":"get_snapshot","execution":False})

def verify_oad_014_kalshi_sequence_integrity_gap_detection_resync():
    good=evaluate_sequence_integrity(2,2,3,"orderbook_delta")
    gap=evaluate_sequence_integrity(2,3,5,"orderbook_delta")
    cmd=build_orderbook_resync_command(9,2,("A",))
    return good.accept and not good.resync_required and gap.resync_required and cmd["params"]["action"]=="get_snapshot"
"""
TEST_SOURCE=r"""
import unittest
from qseries_v2.oracle_adapters.kalshi.oad_014_sequence_integrity import *
class T(unittest.TestCase):
    def test_verifier(self): self.assertTrue(verify_oad_014_kalshi_sequence_integrity_gap_detection_resync())
    def test_duplicate_rejected(self): self.assertFalse(evaluate_sequence_integrity(1,5,5,"ticker").accept)
    def test_snapshot_baseline(self): self.assertTrue(evaluate_sequence_integrity(1,None,10,"orderbook_snapshot").accept)
    def test_gap_resync(self): self.assertTrue(evaluate_sequence_integrity(1,1,3,"orderbook_delta").resync_required)
if __name__=="__main__":
    print("="*72);print(" OAD-014 CERTIFICATION TEST");print(" SEQUENCE INTEGRITY + GAP DETECTION + RESYNC");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] Kalshi sequence integrity/gap detection/get_snapshot resync certified");print("[DONE] OAD-014 CERTIFIED")
"""

def verify_upstream():
    p=PACKAGE/'oad_013_market_data_normalization.py'
    if not p.is_file():
        raise RuntimeError("Certified upstream missing: "+str(p))
    sys.path.insert(0,str(ROOT))
    try:
        importlib.invalidate_caches()
        m=importlib.import_module('qseries_v2.oracle_adapters.kalshi.oad_013_market_data_normalization')
        if getattr(m,'verify_oad_013_kalshi_orderbook_trade_ticker_normalization')() is not True:
            raise RuntimeError("Certified upstream verifier returned false")
    finally:
        if str(ROOT) in sys.path: sys.path.remove(str(ROOT))

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
            name="qseries_v2.oracle_adapters.kalshi."+MODULE.stem
            sys.modules.pop(name,None)
            m=importlib.import_module(name)
            verifier=getattr(m,[x for x in EXPORTS if x.startswith("verify_")][-1])
            if verifier() is not True:
                raise RuntimeError("Production verifier returned false")
        finally:
            if str(ROOT) in sys.path: sys.path.remove(str(ROOT))
        run_test(TEST)
    except Exception:
        for p,old in backups.items():
            if old is None:
                if p.exists(): p.unlink()
            else: p.write_bytes(old)
        print("[ROLLBACK] "+BUILD_ID+" installation failed; affected files restored")
        raise
    manifest={"build_id":BUILD_ID,"revision":REVISION,"module":str(MODULE.relative_to(ROOT)),
              "test":TEST.name,"files":{str(MODULE.relative_to(ROOT)):sha(MODULE),
              TEST.name:sha(TEST),str(INIT.relative_to(ROOT)):sha(INIT)}}
    digest=hashlib.sha256(json.dumps(manifest,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    print("[PASS] Wrote: "+str(MODULE.relative_to(ROOT)))
    print("[PASS] Updated: "+str(INIT.relative_to(ROOT)))
    print("[PASS] Wrote: "+TEST.name)
    print("[PASS] Deterministic install hash: "+digest)
    print("[DONE] "+BUILD_ID+" INSTALLATION AND CERTIFICATION COMPLETE")

if __name__=="__main__": main()
