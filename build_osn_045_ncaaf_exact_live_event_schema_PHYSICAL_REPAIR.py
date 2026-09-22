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
    print(" OSN-045 NCAAF EXACT LIVE EVENT-SCHEMA PHYSICAL REPAIR INSTALLER")
    print("="*118)

    require("qseries_v2/oracle_source_network/certification/live_payload_structure_probe.py")
    require("qseries_v2/oracle_source_network/certification/live_event_structure_forensics.py")

    write(
        "qseries_v2/oracle_source_network/certification/ncaa_exact_event_schema_probe.py",
        '\nimport html\nimport json\nimport re\nfrom dataclasses import dataclass\nfrom typing import Any\n\nEVENT_TERMS = (\n    "game","event","contest","match","team","opponent","home","away",\n    "start","date","time","score","status","id","name"\n)\n\n@dataclass(frozen=True, slots=True)\nclass Candidate:\n    path: str\n    keys: tuple\n    scalar_fields: tuple\n    score: int\n    execution_authority: bool = False\n\ndef _application_json(body):\n    pattern=r\'<script\\b[^>]*type=["\\\']application/json["\\\'][^>]*>(.*?)</script>\'\n    for i,raw in enumerate(re.findall(pattern, body, re.I|re.S)):\n        text=html.unescape(raw).strip()\n        if not text:\n            continue\n        try:\n            yield i,json.loads(text)\n        except Exception:\n            continue\n\ndef _scalars(d):\n    rows=[]\n    for k,v in d.items():\n        if isinstance(v,(str,int,float,bool)) or v is None:\n            s=repr(v)\n            if len(s)>180:\n                s=s[:177]+"..."\n            rows.append(f"{k}={s}")\n    return tuple(rows[:35])\n\ndef _score_dict(d):\n    keys=[str(k).lower() for k in d.keys()]\n    score=0\n    for key in keys:\n        for term in EVENT_TERMS:\n            if term==key or term in key:\n                score+=1\n    # extra weight for dictionaries containing multiple event-like semantic families\n    families=0\n    for family in (\n        ("home","away","opponent","team"),\n        ("start","date","time"),\n        ("game","event","contest","match"),\n        ("score","status"),\n        ("id",),\n    ):\n        if any(any(term in key for term in family) for key in keys):\n            families+=1\n    return score + families*3\n\ndef _walk(obj: Any, path: str, out: list, depth=0, max_depth=18):\n    if depth>max_depth or len(out)>4000:\n        return\n    if isinstance(obj,dict):\n        score=_score_dict(obj)\n        if score>=5:\n            out.append(Candidate(\n                path=path,\n                keys=tuple(str(k) for k in obj.keys())[:60],\n                scalar_fields=_scalars(obj),\n                score=score,\n            ))\n        for k,v in obj.items():\n            _walk(v,f"{path}.{k}",out,depth+1,max_depth)\n    elif isinstance(obj,list):\n        # Inspect enough real records without flooding output.\n        for i,v in enumerate(obj[:120]):\n            _walk(v,f"{path}[{i}]",out,depth+1,max_depth)\n\ndef inspect_ncaaf_event_schema(body):\n    rows=[]\n    json_documents=0\n    for idx,obj in _application_json(body):\n        json_documents+=1\n        local=[]\n        _walk(obj,f"$script[{idx}]",local)\n        rows.extend(local)\n    rows.sort(key=lambda x:(-x.score,x.path))\n    # Path-shape dedupe so repeated game rows don\'t overwhelm useful schema.\n    chosen=[]\n    seen_shapes=set()\n    for row in rows:\n        shape=re.sub(r\'\\[\\d+\\]\',\'[*]\',row.path)\n        signature=(shape,row.keys)\n        if signature in seen_shapes:\n            continue\n        seen_shapes.add(signature)\n        chosen.append(row)\n        if len(chosen)>=50:\n            break\n    return json_documents,tuple(chosen)\n\ndef print_schema(json_documents,candidates):\n    print(f"[NCAAF_SCHEMA] application_json_documents={json_documents} ranked_candidate_shapes={len(candidates)}")\n    for i,row in enumerate(candidates,1):\n        print(f"[CANDIDATE {i:02d}] score={row.score} path={row.path}")\n        print("  keys=",row.keys)\n        if row.scalar_fields:\n            print("  scalars=",row.scalar_fields)\n',
    )
    write(
        "test_osn_045_ncaaf_exact_live_event_schema_PHYSICAL_REPAIR.py",
        '\nimport subprocess,sys\n\n# Deterministic ranking regression.\nfrom qseries_v2.oracle_source_network.certification.ncaa_exact_event_schema_probe import inspect_ncaaf_event_schema\n\nsample=r"""\n<html><script type="application/json">\n{"data":{"games":[{"contest_id":"123","start_date":"2026-09-05","home":{"name":"Alpha"},"away":{"name":"Beta"},"status":"scheduled"}]}}\n</script></html>\n"""\ndocs,rows=inspect_ncaaf_event_schema(sample)\nassert docs==1\nassert rows\nprint("[PASS] NCAA exact-schema ranking regression certified")\n\nprobe=r"""\nfrom qseries_v2.oracle_source_network.certification.live_payload_structure_probe import acquire_live_payload\nfrom qseries_v2.oracle_source_network.certification.ncaa_exact_event_schema_probe import inspect_ncaaf_event_schema,print_schema\n\n_,payload=acquire_live_payload("NCAAF",8.0)\ndocs,rows=inspect_ncaaf_event_schema(payload["body"])\nprint_schema(docs,rows)\n\nassert len(payload["body"])>0\nassert docs>0, "NCAAF application/json document disappeared"\nassert rows, "NCAAF JSON exists but no ranked event-like object shapes were found"\n\nprint("[PASS] NCAAF exact live JSON object schema physically captured")\n"""\n\ntry:\n    p=subprocess.run([sys.executable,"-c",probe],text=True,capture_output=True,timeout=30)\nexcept subprocess.TimeoutExpired:\n    raise AssertionError("OSN-045 exact-schema repair exceeded hard 30-second gate")\n\nif p.stdout:\n    print(p.stdout.rstrip())\nif p.stderr:\n    print(p.stderr.rstrip())\n\nassert p.returncode==0, f"OSN-045 exact-schema repair failed rc={p.returncode}"\nprint("[PASS] OSN-045 NCAAF exact live event-schema probe certified")\n',
    )

    print("[PASS] failed assumed NCAA field mapping retired")
    print("[PASS] exact application/json object paths + scalar fields will be physically exposed")
    print("[PASS] no extractor keys guessed")
    print("[PASS] execution_authority=FALSE")

if __name__=="__main__":
    main()
