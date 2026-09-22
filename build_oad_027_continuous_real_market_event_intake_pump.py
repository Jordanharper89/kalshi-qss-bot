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

BUILD_ID='OAD-027'
TITLE='CONTINUOUS REAL MARKET-EVENT INTAKE PUMP'
REVISION='OAD_027_PRODUCTION_V1'
MODULE=PACKAGE/'oad_027_event_intake_pump.py'
TEST=ROOT/'test_oad_027_continuous_real_market_event_intake_pump.py'
EXPORTS=('OAD_027_BUILD_ID', 'OAD_027_REVISION', 'PumpResult', 'pump_market_messages', 'verify_oad_027_continuous_real_market_event_intake_pump')
MODULE_SOURCE='\nfrom dataclasses import dataclass\nfrom types import MappingProxyType\nfrom .oad_013_market_data_normalization import normalize_kalshi_market_data\nfrom .oad_014_sequence_integrity import evaluate_sequence_integrity\n\nOAD_027_BUILD_ID="OAD-027"\nOAD_027_REVISION="OAD_027_CONTINUOUS_REAL_MARKET_EVENT_INTAKE_PUMP_V1"\n\n@dataclass(frozen=True)\nclass PumpResult:\n    accepted:int\n    rejected:int\n    resync_required:int\n    latest_seq_by_sid:tuple[tuple[int,int],...]\n\ndef pump_market_messages(messages,oracle_receive_ns):\n    seqs={}\n    accepted=rejected=resync=0\n    for raw in messages:\n        typ=str(raw.get("type",""))\n        if typ not in ("orderbook_snapshot","orderbook_delta","ticker","trade"):\n            continue\n        event=normalize_kalshi_market_data(raw,int(oracle_receive_ns))\n        prev=seqs.get(event.sid)\n        d=evaluate_sequence_integrity(event.sid,prev,event.seq,event.event_type)\n        if d.accept:\n            accepted+=1\n            seqs[event.sid]=event.seq\n        else:\n            rejected+=1\n            if d.resync_required: resync+=1\n    return PumpResult(accepted,rejected,resync,tuple(sorted(seqs.items())))\n\ndef verify_oad_027_continuous_real_market_event_intake_pump():\n    msgs=(\n        {"type":"orderbook_snapshot","sid":1,"seq":10,"msg":{"market_ticker":"A"}},\n        {"type":"orderbook_delta","sid":1,"seq":11,"msg":{"market_ticker":"A"}},\n        {"type":"orderbook_delta","sid":1,"seq":13,"msg":{"market_ticker":"A"}},\n    )\n    x=pump_market_messages(msgs,100)\n    return x.accepted==2 and x.rejected==1 and x.resync_required==1\n'
TEST_SOURCE='\nimport unittest\nfrom qseries_v2.oracle_adapters.kalshi.oad_027_event_intake_pump import *\nclass T(unittest.TestCase):\n    def test_verifier(self): self.assertTrue(verify_oad_027_continuous_real_market_event_intake_pump())\n    def test_non_market_ignored(self):\n        x=pump_market_messages(({"type":"subscribed"},),100)\n        self.assertEqual(x.accepted,0)\nif __name__=="__main__":\n    print("="*72);print(" OAD-027 CERTIFICATION TEST");print(" CONTINUOUS REAL MARKET-EVENT INTAKE PUMP");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] Continuous Kalshi market-event intake/sequence pump certified");print("[DONE] OAD-027 CERTIFIED")\n'


def verify_upstream():
    p=PACKAGE/'oad_026_persistent_stream_runner.py'
    if not p.is_file():
        raise RuntimeError("Certified upstream missing: "+str(p))
    sys.path.insert(0,str(ROOT))
    try:
        importlib.invalidate_caches()
        m=importlib.import_module('qseries_v2.oracle_adapters.kalshi.oad_026_persistent_stream_runner')
        if getattr(m,'verify_oad_026_persistent_kalshi_live_stream_runner')() is not True:
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
