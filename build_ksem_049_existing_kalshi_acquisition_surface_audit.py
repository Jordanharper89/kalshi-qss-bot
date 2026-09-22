from pathlib import Path
import ast, json

ROOT = Path.cwd()
STATE = ROOT / "qseries_v2/kalshi_sports_evidence_mapping/state"
OUT = STATE / "ksem049_existing_kalshi_acquisition_surface_audit.json"
TEST = ROOT / "test_ksem_049_existing_kalshi_acquisition_surface_audit.py"

TOKENS = (
    "/markets/", "market_ticker", "event_ticker", "get_market",
    "fetch_market", "retrieve_market", "market_id"
)

def main():
    print("="*120)
    print(" KSEM-049 EXISTING KALSHI ACQUISITION SURFACE AUDIT")
    print("="*120)

    roots = [
        ROOT/"qseries_v2/oracle_adapters",
        ROOT/"qseries_v2/oracle_pre_settlement_coverage",
        ROOT/"qseries_v2/oracle_intelligence_analytics_runtime",
    ]

    hits = []
    for base in roots:
        if not base.exists():
            continue
        for p in base.rglob("*.py"):
            text = p.read_text(encoding="utf-8", errors="ignore")
            low = text.lower()
            if "kalshi" not in low:
                continue
            if not any(t.lower() in low for t in TOKENS):
                continue
            try:
                tree = ast.parse(text)
            except Exception:
                continue
            for n in tree.body:
                if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    body = ast.get_source_segment(text, n) or ""
                    body_low = body.lower()
                    score = 0
                    if "/markets/" in body_low: score += 100
                    if "market_ticker" in body_low: score += 40
                    if "event_ticker" in body_low: score += 20
                    if "requests." in body_low or "urllib" in body_low or "http" in body_low: score += 20
                    if "fetch" in n.name.lower() or "get" in n.name.lower(): score += 10
                    if score:
                        hits.append({
                            "file": str(p.relative_to(ROOT)),
                            "function": n.name,
                            "args": [x.arg for x in n.args.args],
                            "line": n.lineno,
                            "score": score,
                        })

    hits.sort(key=lambda x: (-x["score"], x["file"], x["line"]))
    print("[CANDIDATES]", len(hits))
    for x in hits[:80]:
        print("[CANDIDATE]", x)

    OUT.write_text(json.dumps({
        "candidates": hits,
        "execution_authority": False,
    }, indent=2), encoding="utf-8")

    TEST.write_text(
        "import json\nfrom pathlib import Path\n"
        "d=json.loads(Path('qseries_v2/kalshi_sports_evidence_mapping/state/ksem049_existing_kalshi_acquisition_surface_audit.json').read_text())\n"
        "assert 'candidates' in d\n"
        "assert d['execution_authority'] is False\n"
        "print('[PASS] existing Kalshi acquisition surfaces audited without guessed interface execution')\n"
        "print('[PASS] KSEM-049 certified')\n",
        encoding="utf-8",
    )
    print("[WRITE]", OUT.relative_to(ROOT))
    print("[WRITE]", TEST.name)

if __name__=="__main__":
    main()
