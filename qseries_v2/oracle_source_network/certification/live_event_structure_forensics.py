
from dataclasses import dataclass
import html, json, re
from typing import Any

TOKENS = (
    "eventid","gameid","matchid","hometeam","awayteam","home_team","away_team",
    "starttime","startdate","schedule","fixtures","score","teams","competitors"
)

@dataclass(frozen=True, slots=True)
class ForensicFinding:
    league: str
    json_paths: tuple
    script_signatures: tuple
    token_contexts: tuple
    structured_candidates: int
    execution_authority: bool = False

def _walk(obj: Any, path="$", out=None, limit=1200):
    if out is None:
        out=[]
    if len(out) >= limit:
        return out

    if isinstance(obj, dict):
        keys=tuple(str(k) for k in obj.keys())
        low_keys=tuple(k.lower() for k in keys)

        # A dictionary is interesting if any key either exactly matches
        # or contains one of the known event-bearing tokens.
        hit=any(
            any(token == key or token in key for token in TOKENS)
            for key in low_keys
        )
        if hit:
            out.append((path, keys[:30]))

        for k,v in obj.items():
            _walk(v, f"{path}.{k}", out, limit)
            if len(out) >= limit:
                break

    elif isinstance(obj, list):
        for i,v in enumerate(obj[:80]):
            _walk(v, f"{path}[{i}]", out, limit)
            if len(out) >= limit:
                break

    return out

def _parse_script_json(body):
    results=[]
    for m in re.finditer(r"<script\b([^>]*)>(.*?)</script>", body, re.I|re.S):
        attrs=m.group(1) or ""
        raw=html.unescape(m.group(2) or "").strip()
        if not raw:
            continue

        script_id=""
        mi=re.search(r'\bid=["\']([^"\']+)["\']', attrs, re.I)
        if mi:
            script_id=mi.group(1)

        stype=""
        mt=re.search(r'\btype=["\']([^"\']+)["\']', attrs, re.I)
        if mt:
            stype=mt.group(1)

        if "json" in stype.lower() or raw[:1] in ("{","["):
            try:
                obj=json.loads(raw)
                results.append((script_id,stype,obj))
            except Exception:
                pass
    return results

def _script_signatures(body):
    sigs=[]
    for m in re.finditer(r"<script\b([^>]*)>", body, re.I):
        attrs=m.group(1) or ""

        src=""
        ms=re.search(r'\bsrc=["\']([^"\']+)["\']', attrs, re.I)
        if ms:
            src=ms.group(1)

        typ=""
        mt=re.search(r'\btype=["\']([^"\']+)["\']', attrs, re.I)
        if mt:
            typ=mt.group(1)

        sid=""
        mi=re.search(r'\bid=["\']([^"\']+)["\']', attrs, re.I)
        if mi:
            sid=mi.group(1)

        text="|".join(x for x in (sid,typ,src) if x)
        if text:
            sigs.append(text[:220])
    return tuple(sigs[:60])

def _contexts(body, width=100):
    low=body.lower()
    contexts=[]
    seen=set()

    for token in TOKENS:
        start=0
        hits=0
        while hits < 4:
            idx=low.find(token,start)
            if idx < 0:
                break

            a=max(0,idx-width)
            b=min(len(body),idx+len(token)+width)
            snippet=re.sub(r"\s+"," ",body[a:b])
            snippet=snippet.replace("\n"," ").replace("\r"," ")
            key=(token,snippet)

            if key not in seen:
                seen.add(key)
                contexts.append(f"{token}: {snippet[:260]}")

            hits+=1
            start=idx+len(token)

    return tuple(contexts[:40])

def inspect_payload(league, body):
    paths=[]

    for sid,stype,obj in _parse_script_json(body):
        label=f"script[id={sid or '-'} type={stype or '-'}]"
        for path,keys in _walk(obj):
            paths.append(f"{label} {path} keys={keys}")
            if len(paths) >= 80:
                break
        if len(paths) >= 80:
            break

    return ForensicFinding(
        league=league,
        json_paths=tuple(paths),
        script_signatures=_script_signatures(body),
        token_contexts=_contexts(body),
        structured_candidates=len(paths),
    )

def print_finding(f):
    print(f"[FORENSIC] {f.league} structured_candidates={f.structured_candidates}")

    if f.json_paths:
        print("[JSON_PATHS]")
        for x in f.json_paths[:30]:
            print(" ",x)

    if f.script_signatures:
        print("[SCRIPT_SIGNATURES]")
        for x in f.script_signatures[:20]:
            print(" ",x)

    if f.token_contexts:
        print("[TOKEN_CONTEXTS]")
        for x in f.token_contexts[:24]:
            print(" ",x)
