from __future__ import annotations
import json,subprocess,sys,time
def probe(root,seconds=8.0):
 stop=root/"runtime_state/solana_intelligence/STOP_OSI_LIVE"
 if stop.exists():stop.unlink()
 p=subprocess.Popen([sys.executable,str(root/"run_osi_solana_intelligence_live.py")],cwd=str(root))
 time.sleep(float(seconds))
 stop.parent.mkdir(parents=True,exist_ok=True);stop.write_text("SULS-086 bounded physical probe\n",encoding="utf-8")
 try:rc=p.wait(timeout=10)
 except subprocess.TimeoutExpired:
  p.terminate()
  try:rc=p.wait(timeout=5)
  except subprocess.TimeoutExpired:p.kill();rc=p.wait(timeout=5)
 status=root/"runtime_state/solana_opportunities/launch_surveillance/persistent_event_driven_runtime_status.json"
 d=json.loads(status.read_text(encoding="utf-8")) if status.exists() else {}
 if stop.exists():stop.unlink()
 return {"revision":"SULS_086","child_returncode":rc,"status_found":status.exists(),
  "suls_connected":bool(d.get("connected")),"ack_count":int(d.get("ack_count",0)),
  "notifications":int(d.get("notifications",0)),"execution_authority":False,"read_only":True}
def write(root):
 d=probe(root);p=root/"runtime_state/solana_opportunities/launch_surveillance/bounded_osi_child_physical_probe.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
