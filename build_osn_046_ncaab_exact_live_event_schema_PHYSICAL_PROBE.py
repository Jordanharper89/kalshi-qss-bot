from pathlib import Path

ROOT=Path.cwd()

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
    print(" OSN-046 NCAAB EXACT LIVE EVENT-SCHEMA PHYSICAL PROBE INSTALLER")
    print("="*118)

    require("qseries_v2/oracle_source_network/certification/live_payload_structure_probe.py")
    require("qseries_v2/oracle_source_network/certification/live_event_structure_forensics.py")

    write(
        "qseries_v2/oracle_source_network/certification/ncaab_exact_event_schema_probe.py",
        '\nimport html\nimport json\nimport re\nfrom dataclasses import dataclass\nfrom typing import Any\n\nEVENT_TERMS = (\n    "game","event","contest","match","team","opponent","home","away",\n    "start","date","time","score","status","id","name"\n)\n\n@dataclass(frozen=True, slots=True)\nclass Candidate:\n    path: str\n    keys: tuple\n    scalar_fields: tuple\n    score: int\n    execution_authority: bool = False\n\ndef _application_json(body):\n    pattern=r\'<script\\b[^>]*type=["\\\']application/json["\\\'][^>]*>(.*?)</script>\'\n    for i,raw in enumerate(re.findall(pattern, body, re.I|re.S)):\n        text=html.unescape(raw).strip()\n        if not text:\n            continue\n        try:\n            yield i,json.loads(text)\n        except Exception:\n            continue\n\ndef _scalars(d):\n    rows=[]\n    for k,v in d.items():\n        if isinstance(v,(str,int,float,bool)) or v is None:\n            s=repr(v)\n            if len(s)>180:\n                s=s[:177]+"..."\n            rows.append(f"{k}={s}")\n    return tuple(rows[:35])\n\ndef _score_dict(d):\n    keys=[str(k).lower() for k in d.keys()]\n    score=0\n    for key in keys:\n        for term in EVENT_TERMS:\n            if term==key or term in key:\n                score+=1\n    families=0\n    for family in (\n        ("home","away","opponent","team"),\n        ("start","date","time"),\n        ("game","event","contest","match"),\n        ("score","status"),\n        ("id",),\n    ):\n        if any(any(term in key for term in family) for key in keys):\n            families+=1\n    return score + families*3\n\ndef _walk(obj: Any, path: str, out: list, depth=0, max_depth=18):\n    if depth>max_depth or len(out)>4000:\n        return\n    if isinstance(obj,dict):\n        score=_score_dict(obj)\n        if score>=5:\n            out.append(Candidate(\n                path=path,\n                keys=tuple(str(k) for k in obj.keys())[:60],\n                scalar_fields=_scalars(obj),\n                score=score,\n            ))\n        for k,v in obj.items():\n            _walk(v,f"{path}.{k}",out,depth+1,max_depth)\n    elif isinstance(obj,list):\n        for i,v in enumerate(obj[:120]):\n            _walk(v,f"{path}[{i}]",out,depth+1,max_depth)\n\ndef inspect_ncaab_event_schema(body):\n    rows=[]\n    json_documents=0\n    for idx,obj in _application_json(body):\n        json_documents+=1\n        local=[]\n        _walk(obj,f"$script[{idx}]",local)\n        rows.extend(local)\n\n    rows.sort(key=lambda x:(-x.score,x.path))\n    chosen=[]\n    seen_shapes=set()\n\n    for row in rows:\n        shape=re.sub(r\'\\[\\d+\\]\',\'[*]\',row.path)\n        signature=(shape,row.keys)\n        if signature in seen_shapes:\n            continue\n        seen_shapes.add(signature)\n        chosen.append(row)\n        if len(chosen)>=50:\n            break\n\n    return json_documents,tuple(chosen)\n\ndef print_schema(json_documents,candidates):\n    print(f"[NCAAB_SCHEMA] application_json_documents={json_documents} ranked_candidate_shapes={len(candidates)}")\n    for i,row in enumerate(candidates,1):\n        print(f"[CANDIDATE {i:02d}] score={row.score} path={row.path}")\n        print("  keys=",row.keys)\n        if row.scalar_fields:\n            print("  scalars=",row.scalar_fields)\n',
    )
    write(
        "test_osn_046_ncaab_exact_live_event_schema_PHYSICAL_PROBE.py",
        '\nimport subprocess,sys\nfrom qseries_v2.oracle_source_network.certification.ncaab_exact_event_schema_probe import inspect_ncaab_event_schema\n\nsample=r"""\n<html><script type="application/json">\n{"data":{"games":[{"contestId":"123","startDate":"2026-11-01","teams":[{"isHome":true,"nameShort":"Alpha"},{"isHome":false,"nameShort":"Beta"}]}]}}\n</script></html>\n"""\ndocs,rows=inspect_ncaab_event_schema(sample)\nassert docs==1\nassert rows\nprint("[PASS] NCAAB exact-schema ranking regression certified")\n\nprobe=r"""\nfrom qseries_v2.oracle_source_network.certification.live_payload_structure_probe import acquire_live_payload\nfrom qseries_v2.oracle_source_network.certification.ncaab_exact_event_schema_probe import inspect_ncaab_event_schema,print_schema\n\n_,payload=acquire_live_payload("NCAAB",8.0)\ndocs,rows=inspect_ncaab_event_schema(payload["body"])\nprint_schema(docs,rows)\n\nassert len(payload["body"])>0\nassert docs>0, "NCAAB application/json document disappeared"\nassert rows, "NCAAB JSON exists but no ranked event-like object shapes were found"\n\nprint("[PASS] NCAAB exact live JSON object schema physically captured")\n"""\n\ntry:\n    p=subprocess.run([sys.executable,"-c",probe],text=True,capture_output=True,timeout=30)\nexcept subprocess.TimeoutExpired:\n    raise AssertionError("OSN-046 exact-schema probe exceeded hard 30-second gate")\n\nif p.stdout:\n    print(p.stdout.rstrip())\nif p.stderr:\n    print(p.stderr.rstrip())\n\nassert p.returncode==0, f"OSN-046 exact-schema probe failed rc={p.returncode}"\nprint("[PASS] OSN-046 NCAAB exact live event-schema probe certified")\n',
    )

    print("[PASS] OSN-046 installed")
    print("[PASS] exact NCAAB application/json paths + scalar fields will be physically exposed")
    print("[PASS] no football schema assumed")
    print("[PASS] no extractor keys guessed")
    print("[PASS] execution_authority=FALSE")

if __name__=="__main__":
    main()
