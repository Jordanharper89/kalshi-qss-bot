from pathlib import Path

ROOT=Path.cwd()

def require(rel):
    p=ROOT/rel
    if not p.exists(): raise SystemExit('[FAIL] missing dependency: '+str(p))
    print('[PASS] dependency verified:',p.relative_to(ROOT))

def write(rel,content):
    p=ROOT/rel
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(content.rstrip()+'\n',encoding='utf-8')
    print('[WRITE]',p.relative_to(ROOT))

def main():
    print('='*118)
    print(' OSN-052 MLS OFFICIAL STATS EVENT SURFACE PHYSICAL PROBE INSTALLER')
    print('='*118)
    require('qseries_v2/oracle_source_network/acquisition/soccer_event_surface_boundary.py')
    write('qseries_v2/oracle_source_network/certification/mls_official_stats_event_surface_probe.py','\nimport json,re,urllib.request\nBASE="https://stats-api.mlssoccer.com"\nSEASONS_URI=BASE+"/competitions/MLS-COM-000001/seasons"\n\ndef _get(uri,timeout=8.0):\n    req=urllib.request.Request(uri,headers={"User-Agent":"Mozilla/5.0","Accept":"application/json"})\n    with urllib.request.urlopen(req,timeout=timeout) as r: raw=r.read()\n    return raw,json.loads(raw.decode("utf-8"))\n\ndef _walk(obj,path="$",depth=0):\n    if depth>8:return\n    if isinstance(obj,dict):\n        yield path,obj\n        for k,v in obj.items(): yield from _walk(v,f"{path}.{k}",depth+1)\n    elif isinstance(obj,list):\n        for i,v in enumerate(obj[:80]): yield from _walk(v,f"{path}[{i}]",depth+1)\n\ndef discover_2026_season(root):\n    candidates=[]\n    for path,d in _walk(root):\n        text=json.dumps(d,ensure_ascii=False)[:2000]\n        if "2026" not in text: continue\n        for k,v in d.items():\n            if isinstance(v,str) and ("SEA" in v.upper() or "season" in k.lower()):\n                candidates.append((path,k,v))\n    # Current 2026 MLS season id observed in public MLS API consumers.\n    for _,_,v in candidates:\n        if v=="MLS-SEA-0001KA": return v\n    for _,_,v in candidates:\n        if isinstance(v,str) and v.startswith("MLS-SEA-"): return v\n    return None\n\ndef probe_surface(timeout=8.0):\n    sraw,sroot=_get(SEASONS_URI,timeout)\n    sid=discover_2026_season(sroot)\n    if not sid: return {"season_bytes":len(sraw),"season_id":None,"matches_uri":None,"match_bytes":0,"sample_paths":[]}\n    muri=BASE+f"/matches/seasons/{sid}"\n    mraw,mroot=_get(muri,timeout)\n    rows=[]\n    for path,d in _walk(mroot):\n        keys=tuple(str(k) for k in d.keys())\n        low=" ".join(k.lower() for k in keys)\n        if any(x in low for x in ("match","home","away","date","score","status","club")):\n            scalars=tuple(f"{k}={repr(v)[:100]}" for k,v in d.items() if isinstance(v,(str,int,float,bool)) or v is None)[:25]\n            rows.append((path,keys[:40],scalars))\n        if len(rows)>=12: break\n    return {"season_bytes":len(sraw),"season_id":sid,"matches_uri":muri,"match_bytes":len(mraw),"sample_paths":rows}\n')
    write('test_osn_052_mls_official_stats_event_surface_physical_probe.py','\nimport subprocess,sys\nprobe=r"""\nfrom qseries_v2.oracle_source_network.certification.mls_official_stats_event_surface_probe import probe_surface\nr=probe_surface(timeout=8.0)\nprint(f"[PHYSICAL] MLS season_bytes={r[\'season_bytes\']} season_id={r[\'season_id\']} match_bytes={r[\'match_bytes\']} uri={r[\'matches_uri\']}")\nfor i,(path,keys,scalars) in enumerate(r["sample_paths"],1):\n    print(f"[MLS_CANDIDATE {i:02d}] path={path}")\n    print("  keys=",keys)\n    if scalars: print("  scalars=",scalars)\nassert r["season_bytes"]>0\nassert r["season_id"],"MLS-owned seasons API did not expose a 2026 season id"\nassert r["match_bytes"]>0,"MLS-owned 2026 season match endpoint returned no payload"\nassert r["sample_paths"],"MLS match payload returned but no event-like object shapes were found"\nprint("[PASS] MLS-owned 2026 production match surface physically proven")\nprint("[HOLD] MLS canonical extraction remains closed until exact printed match schema is mapped")\n"""\np=subprocess.run([sys.executable,"-c",probe],text=True,capture_output=True,timeout=30)\nif p.stdout: print(p.stdout.rstrip())\nif p.stderr: print(p.stderr.rstrip())\nassert p.returncode==0,f"OSN-052 failed rc={p.returncode}"\nprint("[PASS] OSN-052 MLS official stats event-surface probe certified")\n')
    print('[PASS] MLS-owned stats API probe installed')
    print('[PASS] exact live match schema will be printed before extractor construction')
    print('[PASS] execution_authority=FALSE')

if __name__=='__main__': main()
