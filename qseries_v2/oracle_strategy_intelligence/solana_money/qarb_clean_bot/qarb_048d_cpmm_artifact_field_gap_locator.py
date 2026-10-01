from pathlib import Path
import json

NEED=("pool","token_a","token_b","vault_a","vault_b")

def walk(x):
    if isinstance(x,dict):
        yield x
        for v in x.values(): yield from walk(v)
    elif isinstance(x,list):
        for v in x: yield from walk(v)

def main():
    root=Path.cwd()/"runtime_state"
    hits=0
    print("[QARB-048D] CPMM ARTIFACT FIELD-GAP LOCATOR")
    for p in root.rglob("*.json"):
        try:d=json.loads(p.read_text(encoding="utf-8"))
        except Exception:continue
        rows=[]
        for x in walk(d):
            venue=str(x.get("venue") or x.get("venue_name") or
                      x.get("family") or "").upper()
            if venue not in ("RAYDIUM_CPMM","CPMM"):continue
            rows.append(x)
        if not rows:continue
        print("\n[FILE]",p.relative_to(Path.cwd()))
        for x in rows[:8]:
            keys=sorted(x.keys())
            present={k:(k in x and x.get(k) not in (None,"")) for k in NEED}
            aliases={k:x.get(k) for k in
                     ("pool","pool_id","pool_address",
                      "token_a","token_b","mint_a","mint_b",
                      "input_mint","output_mint","base_mint","quote_mint",
                      "vault_a","vault_b","base_vault","quote_vault",
                      "token_vault_a","token_vault_b")
                     if x.get(k) not in (None,"")}
            print("[CPMM_ROW] present=",present)
            print("[ALIASES]",json.dumps(aliases,sort_keys=True))
            print("[KEYS]",keys)
            hits+=1
    print("\n[CPMM_ROWS_FOUND]",hits)
    print("[MODE] SOURCE_CAPTURE_ONLY execution_authority=FALSE")

if __name__=="__main__":main()
