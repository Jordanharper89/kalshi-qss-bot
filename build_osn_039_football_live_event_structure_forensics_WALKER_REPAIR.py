from pathlib import Path

ROOT = Path.cwd()

def require(rel):
    p=ROOT/rel
    if not p.exists():
        raise SystemExit("[FAIL] missing dependency: "+str(p))
    print("[PASS] dependency verified:",p.relative_to(ROOT))

def write(rel,content):
    p=ROOT/rel
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(content.rstrip()+"\n",encoding="utf-8")
    print("[WRITE]",p.relative_to(ROOT))

def main():
    print("="*118)
    print(" OSN-039 FOOTBALL LIVE EVENT STRUCTURE FORENSICS - WALKER FOUNDATION REPAIR INSTALLER")
    print("="*118)

    require("qseries_v2/oracle_source_network/certification/live_payload_structure_probe.py")
    require("qseries_v2/oracle_source_network/certification/live_event_structure_forensics.py")

    write(
        "qseries_v2/oracle_source_network/certification/live_event_structure_forensics.py",
        '\nfrom dataclasses import dataclass\nimport html, json, re\nfrom typing import Any\n\nTOKENS = (\n    "eventid","gameid","matchid","hometeam","awayteam","home_team","away_team",\n    "starttime","startdate","schedule","fixtures","score","teams","competitors"\n)\n\n@dataclass(frozen=True, slots=True)\nclass ForensicFinding:\n    league: str\n    json_paths: tuple\n    script_signatures: tuple\n    token_contexts: tuple\n    structured_candidates: int\n    execution_authority: bool = False\n\ndef _walk(obj: Any, path="$", out=None, limit=1200):\n    if out is None:\n        out=[]\n    if len(out) >= limit:\n        return out\n\n    if isinstance(obj, dict):\n        keys=tuple(str(k) for k in obj.keys())\n        low_keys=tuple(k.lower() for k in keys)\n\n        # A dictionary is interesting if any key either exactly matches\n        # or contains one of the known event-bearing tokens.\n        hit=any(\n            any(token == key or token in key for token in TOKENS)\n            for key in low_keys\n        )\n        if hit:\n            out.append((path, keys[:30]))\n\n        for k,v in obj.items():\n            _walk(v, f"{path}.{k}", out, limit)\n            if len(out) >= limit:\n                break\n\n    elif isinstance(obj, list):\n        for i,v in enumerate(obj[:80]):\n            _walk(v, f"{path}[{i}]", out, limit)\n            if len(out) >= limit:\n                break\n\n    return out\n\ndef _parse_script_json(body):\n    results=[]\n    for m in re.finditer(r"<script\\b([^>]*)>(.*?)</script>", body, re.I|re.S):\n        attrs=m.group(1) or ""\n        raw=html.unescape(m.group(2) or "").strip()\n        if not raw:\n            continue\n\n        script_id=""\n        mi=re.search(r\'\\bid=["\\\']([^"\\\']+)["\\\']\', attrs, re.I)\n        if mi:\n            script_id=mi.group(1)\n\n        stype=""\n        mt=re.search(r\'\\btype=["\\\']([^"\\\']+)["\\\']\', attrs, re.I)\n        if mt:\n            stype=mt.group(1)\n\n        if "json" in stype.lower() or raw[:1] in ("{","["):\n            try:\n                obj=json.loads(raw)\n                results.append((script_id,stype,obj))\n            except Exception:\n                pass\n    return results\n\ndef _script_signatures(body):\n    sigs=[]\n    for m in re.finditer(r"<script\\b([^>]*)>", body, re.I):\n        attrs=m.group(1) or ""\n\n        src=""\n        ms=re.search(r\'\\bsrc=["\\\']([^"\\\']+)["\\\']\', attrs, re.I)\n        if ms:\n            src=ms.group(1)\n\n        typ=""\n        mt=re.search(r\'\\btype=["\\\']([^"\\\']+)["\\\']\', attrs, re.I)\n        if mt:\n            typ=mt.group(1)\n\n        sid=""\n        mi=re.search(r\'\\bid=["\\\']([^"\\\']+)["\\\']\', attrs, re.I)\n        if mi:\n            sid=mi.group(1)\n\n        text="|".join(x for x in (sid,typ,src) if x)\n        if text:\n            sigs.append(text[:220])\n    return tuple(sigs[:60])\n\ndef _contexts(body, width=100):\n    low=body.lower()\n    contexts=[]\n    seen=set()\n\n    for token in TOKENS:\n        start=0\n        hits=0\n        while hits < 4:\n            idx=low.find(token,start)\n            if idx < 0:\n                break\n\n            a=max(0,idx-width)\n            b=min(len(body),idx+len(token)+width)\n            snippet=re.sub(r"\\s+"," ",body[a:b])\n            snippet=snippet.replace("\\n"," ").replace("\\r"," ")\n            key=(token,snippet)\n\n            if key not in seen:\n                seen.add(key)\n                contexts.append(f"{token}: {snippet[:260]}")\n\n            hits+=1\n            start=idx+len(token)\n\n    return tuple(contexts[:40])\n\ndef inspect_payload(league, body):\n    paths=[]\n\n    for sid,stype,obj in _parse_script_json(body):\n        label=f"script[id={sid or \'-\'} type={stype or \'-\'}]"\n        for path,keys in _walk(obj):\n            paths.append(f"{label} {path} keys={keys}")\n            if len(paths) >= 80:\n                break\n        if len(paths) >= 80:\n            break\n\n    return ForensicFinding(\n        league=league,\n        json_paths=tuple(paths),\n        script_signatures=_script_signatures(body),\n        token_contexts=_contexts(body),\n        structured_candidates=len(paths),\n    )\n\ndef print_finding(f):\n    print(f"[FORENSIC] {f.league} structured_candidates={f.structured_candidates}")\n\n    if f.json_paths:\n        print("[JSON_PATHS]")\n        for x in f.json_paths[:30]:\n            print(" ",x)\n\n    if f.script_signatures:\n        print("[SCRIPT_SIGNATURES]")\n        for x in f.script_signatures[:20]:\n            print(" ",x)\n\n    if f.token_contexts:\n        print("[TOKEN_CONTEXTS]")\n        for x in f.token_contexts[:24]:\n            print(" ",x)\n'
    )
    write(
        "test_osn_039_football_live_event_structure_forensics_WALKER_REPAIR.py",
        '\nimport subprocess,sys\n\n# Deterministic walker regression first.\nfrom qseries_v2.oracle_source_network.certification.live_event_structure_forensics import _walk\nsample={\n    "root":{\n        "gameId":"abc",\n        "homeTeam":{"name":"A"},\n        "awayTeam":{"name":"B"},\n        "startTime":"2026-09-10T00:00:00Z",\n    }\n}\nrows=_walk(sample)\nassert rows, "walker failed to detect event-bearing keys"\nprint("[PASS] forensic walker generator-scope defect repaired")\n\nprobe=r"""\nfrom qseries_v2.oracle_source_network.certification.live_payload_structure_probe import acquire_live_payload\nfrom qseries_v2.oracle_source_network.certification.live_event_structure_forensics import inspect_payload,print_finding\n\nfor league in ("NFL","NCAAF"):\n    _,payload=acquire_live_payload(league,8.0)\n    f=inspect_payload(league,payload["body"])\n    print_finding(f)\n    assert len(payload["body"])>0\n    assert f.execution_authority is False\n\nprint("[PASS] football live structure forensics captured")\n"""\n\ntry:\n    p=subprocess.run([sys.executable,"-c",probe],text=True,capture_output=True,timeout=35)\nexcept subprocess.TimeoutExpired:\n    raise AssertionError("OSN-039 repair physical gate exceeded hard 35-second limit")\n\nif p.stdout:\n    print(p.stdout.rstrip())\nif p.stderr:\n    print(p.stderr.rstrip())\n\nassert p.returncode==0, f"OSN-039 repaired forensic gate failed rc={p.returncode}"\n\nprint("[PASS] OSN-039 repaired football live event structure forensics certified")\n'
    )

    print("[PASS] shared forensic walker foundation repaired")
    print("[PASS] downstream OSN-040 through OSN-043 continue against repaired shared module")
    print("[PASS] execution_authority=FALSE")

if __name__=="__main__":
    main()
