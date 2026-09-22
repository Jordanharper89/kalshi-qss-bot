
import html
import json
import re
from dataclasses import dataclass
from typing import Any

EVENT_TERMS = (
    "game","event","contest","match","team","opponent","home","away",
    "start","date","time","score","status","id","name"
)

@dataclass(frozen=True, slots=True)
class Candidate:
    path: str
    keys: tuple
    scalar_fields: tuple
    score: int
    execution_authority: bool = False

def _application_json(body):
    pattern=r'<script\b[^>]*type=["\']application/json["\'][^>]*>(.*?)</script>'
    for i,raw in enumerate(re.findall(pattern, body, re.I|re.S)):
        text=html.unescape(raw).strip()
        if not text:
            continue
        try:
            yield i,json.loads(text)
        except Exception:
            continue

def _scalars(d):
    rows=[]
    for k,v in d.items():
        if isinstance(v,(str,int,float,bool)) or v is None:
            s=repr(v)
            if len(s)>180:
                s=s[:177]+"..."
            rows.append(f"{k}={s}")
    return tuple(rows[:35])

def _score_dict(d):
    keys=[str(k).lower() for k in d.keys()]
    score=0
    for key in keys:
        for term in EVENT_TERMS:
            if term==key or term in key:
                score+=1
    families=0
    for family in (
        ("home","away","opponent","team"),
        ("start","date","time"),
        ("game","event","contest","match"),
        ("score","status"),
        ("id",),
    ):
        if any(any(term in key for term in family) for key in keys):
            families+=1
    return score + families*3

def _walk(obj: Any, path: str, out: list, depth=0, max_depth=18):
    if depth>max_depth or len(out)>4000:
        return
    if isinstance(obj,dict):
        score=_score_dict(obj)
        if score>=5:
            out.append(Candidate(
                path=path,
                keys=tuple(str(k) for k in obj.keys())[:60],
                scalar_fields=_scalars(obj),
                score=score,
            ))
        for k,v in obj.items():
            _walk(v,f"{path}.{k}",out,depth+1,max_depth)
    elif isinstance(obj,list):
        for i,v in enumerate(obj[:120]):
            _walk(v,f"{path}[{i}]",out,depth+1,max_depth)

def inspect_ncaab_event_schema(body):
    rows=[]
    json_documents=0
    for idx,obj in _application_json(body):
        json_documents+=1
        local=[]
        _walk(obj,f"$script[{idx}]",local)
        rows.extend(local)

    rows.sort(key=lambda x:(-x.score,x.path))
    chosen=[]
    seen_shapes=set()

    for row in rows:
        shape=re.sub(r'\[\d+\]','[*]',row.path)
        signature=(shape,row.keys)
        if signature in seen_shapes:
            continue
        seen_shapes.add(signature)
        chosen.append(row)
        if len(chosen)>=50:
            break

    return json_documents,tuple(chosen)

def print_schema(json_documents,candidates):
    print(f"[NCAAB_SCHEMA] application_json_documents={json_documents} ranked_candidate_shapes={len(candidates)}")
    for i,row in enumerate(candidates,1):
        print(f"[CANDIDATE {i:02d}] score={row.score} path={row.path}")
        print("  keys=",row.keys)
        if row.scalar_fields:
            print("  scalars=",row.scalar_fields)
