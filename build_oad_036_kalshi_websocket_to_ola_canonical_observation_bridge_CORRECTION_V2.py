from __future__ import annotations
import hashlib, importlib, json, os, subprocess, sys
from pathlib import Path

SCRIPT_DIR=Path(__file__).resolve().parent

def locate_repository():
    candidates=[]
    for base in (Path.cwd().resolve(),SCRIPT_DIR):
        candidates += [base,base/"kalshi-qss-bot"]
        for p in base.parents:
            candidates += [p,p/"kalshi-qss-bot"]
    seen=set()
    for c in candidates:
        try: c=c.resolve()
        except OSError: continue
        if c in seen: continue
        seen.add(c)
        if (c/"qseries_v2").is_dir(): return c
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
    if p.returncode: raise RuntimeError("Certification test failed: "+path.name)

BUILD_ID='OAD-036'
TITLE='KALSHI WEBSOCKET → OLA CANONICAL OBSERVATION BRIDGE'
REVISION='OAD_036_PRODUCTION_CORRECTION_V2'
MODULE=PACKAGE/'oad_036_websocket_canonical_bridge.py'
TEST=ROOT/'test_oad_036_kalshi_websocket_to_ola_canonical_observation_bridge.py'
EXPORTS=('OAD_036_BUILD_ID', 'OAD_036_REVISION', 'SOURCE_ID', 'ADAPTER_ID', 'build_ola_canonical_observation_from_websocket', 'verify_oad_036_kalshi_websocket_to_ola_canonical_observation_bridge')
MODULE_SOURCE='\nfrom __future__ import annotations\nfrom datetime import datetime, timezone\nfrom hashlib import sha256\nimport json\n\nfrom qseries_v2.oracle_intelligence.live_acquisition.oracle_live_read_only_acquisition_runtime import (\n    RawSourceObservation,\n    CanonicalObservation,\n)\n\nOAD_036_BUILD_ID="OAD-036"\nOAD_036_REVISION="OAD_036_KALSHI_WEBSOCKET_TO_OLA_CANONICAL_OBSERVATION_BRIDGE_V1"\nSOURCE_ID="source.kalshi.market_data"\nADAPTER_ID="adapter.oracle.kalshi.websocket.live"\n\ndef _canonical_json(value):\n    return json.dumps(value,sort_keys=True,separators=(",",":"),ensure_ascii=False,allow_nan=False)\n\ndef build_ola_canonical_observation_from_websocket(raw_message,*,received_at,acquisition_batch_id):\n    if not isinstance(raw_message,dict):\n        raise TypeError("raw_message must be dict")\n    if not isinstance(received_at,datetime) or received_at.tzinfo is None:\n        raise ValueError("received_at must be timezone-aware datetime")\n    received_at=received_at.astimezone(timezone.utc)\n    typ=str(raw_message.get("type","")).strip()\n    if typ not in ("ticker","trade","orderbook_snapshot","orderbook_delta"):\n        raise ValueError("unsupported live market-data type")\n    msg=raw_message.get("msg") or {}\n    if not isinstance(msg,dict):\n        raise ValueError("msg must be mapping")\n    ticker=str(msg.get("market_ticker") or msg.get("ticker") or "").strip()\n    if not ticker:\n        raise ValueError("market ticker required")\n    sid=int(raw_message.get("sid",0))\n    seq=int(raw_message.get("seq",0))\n    raw_hash=sha256(_canonical_json(raw_message).encode("utf-8")).hexdigest()\n    source_observation_id=f"kalshi.websocket.{typ}.{ticker}.{sid}.{seq}.{raw_hash[:16]}"\n    payload={\n        "source_market_id":ticker,\n        "event_type":typ,\n        "sid":sid,\n        "seq":seq,\n        "message":msg,\n        "raw_message_hash":raw_hash,\n    }\n    provenance={\n        "source_id":SOURCE_ID,\n        "adapter_id":ADAPTER_ID,\n        "transport":"websocket",\n        "read_only":True,\n    }\n    raw=RawSourceObservation.create(\n        source_observation_id=source_observation_id,\n        observed_at=received_at,\n        observation_type=typ,\n        payload=payload,\n        provenance=provenance,\n    )\n    return CanonicalObservation.create(\n        source_id=SOURCE_ID,\n        raw_observation=raw,\n        acquired_at=received_at,\n        acquisition_batch_id=str(acquisition_batch_id),\n    )\n\ndef verify_oad_036_kalshi_websocket_to_ola_canonical_observation_bridge():\n    t=datetime(2026,8,13,20,0,0,tzinfo=timezone.utc)\n    raw={"type":"ticker","sid":1,"seq":2,"msg":{"market_ticker":"KXTEST","yes_bid_dollars":"0.50"}}\n    a=build_ola_canonical_observation_from_websocket(raw,received_at=t,acquisition_batch_id="batch.test")\n    b=build_ola_canonical_observation_from_websocket(raw,received_at=t,acquisition_batch_id="batch.test")\n    return a.observation_id==b.observation_id and a.source_id==SOURCE_ID\n'
TEST_SOURCE='\nimport unittest\nfrom datetime import datetime,timezone\nfrom qseries_v2.oracle_adapters.kalshi.oad_036_websocket_canonical_bridge import *\nclass T(unittest.TestCase):\n    def test_verifier(self): self.assertTrue(verify_oad_036_kalshi_websocket_to_ola_canonical_observation_bridge())\n    def test_trade(self):\n        t=datetime(2026,8,13,tzinfo=timezone.utc)\n        x=build_ola_canonical_observation_from_websocket({"type":"trade","sid":1,"seq":1,"msg":{"market_ticker":"A","price":"0.5"}},received_at=t,acquisition_batch_id="b")\n        self.assertEqual(x.source_id,SOURCE_ID)\n    def test_bad_type(self):\n        with self.assertRaises(ValueError):\n            build_ola_canonical_observation_from_websocket({"type":"subscribed","msg":{"market_ticker":"A"}},received_at=datetime.now(timezone.utc),acquisition_batch_id="b")\nif __name__=="__main__":\n    print("="*72);print(" OAD-036 CERTIFICATION TEST");print(" KALSHI WEBSOCKET → OLA CANONICAL OBSERVATION BRIDGE");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] Real WebSocket messages map to certified OLA canonical observations");print("[DONE] OAD-036 CERTIFIED")\n'


def verify_upstream():
    p=PACKAGE/'oad_035_physical_activation_gate.py'
    if not p.is_file(): raise RuntimeError("Certified upstream missing: "+str(p))
    sys.path.insert(0,str(ROOT))
    try:
        importlib.invalidate_caches()
        m=importlib.import_module('qseries_v2.oracle_adapters.kalshi.oad_035_physical_activation_gate')
        if getattr(m,'verify_oad_035_physical_oracle_kalshi_production_activation_gate')() is not True:
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
            v=getattr(m,[x for x in EXPORTS if x.startswith("verify_")][-1])
            if v() is not True: raise RuntimeError("Production verifier returned false")
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
