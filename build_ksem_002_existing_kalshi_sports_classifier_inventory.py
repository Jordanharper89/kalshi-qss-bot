from pathlib import Path
ROOT=Path.cwd()
PKG=ROOT/"qseries_v2/kalshi_sports_evidence_mapping"
TEST=ROOT/"test_ksem_002_existing_kalshi_sports_classifier_inventory.py"
def main():
    print("="*110); print(" KSEM-002 EXISTING KALSHI SPORTS CLASSIFIER INVENTORY"); print("="*110)
    import json,hashlib,re
    if not (PKG/"state/ksem001_admission_foundation.json").exists(): raise SystemExit("[FAIL] missing KSEM-001")
    terms=("sport","league","team","player","classifier","classification","market_type","decompos","entity")
    hits=[]
    for p in (ROOT/"qseries_v2").rglob("*.py"):
        if "kalshi_sports_evidence_mapping" in str(p).lower(): continue
        text=p.read_text(encoding="utf-8",errors="ignore"); low=text.lower()
        score=sum(t in low for t in terms)
        if score>=4 and ("kalshi" in low or "sports" in low):
            hits.append({"path":str(p.relative_to(ROOT)),"score":score,"sha256":hashlib.sha256(p.read_bytes()).hexdigest(),"symbols":re.findall(r"^(?:def|class)\\s+([A-Za-z_]\\w*)",text,re.M)[:40]})
    hits.sort(key=lambda x:(-x["score"],x["path"]))
    if not hits: raise SystemExit("[FAIL] no existing Kalshi/sports pavement found; refusing guessed dependency")
    state=PKG/"state/ksem002_existing_classifier_inventory.json"; state.write_text(json.dumps({"count":len(hits),"candidates":hits[:80],"execution_authority":False},indent=2))
    print("[FOUND]",len(hits),"physical candidates")
    for x in hits[:20]: print("[CANDIDATE]",x["score"],x["path"])
    TEST.write_text("import json\nfrom pathlib import Path\nd=json.loads(Path('qseries_v2/kalshi_sports_evidence_mapping/state/ksem002_existing_classifier_inventory.json').read_text())\nassert d['count']>0 and d['execution_authority'] is False\nassert all(Path(x['path']).exists() for x in d['candidates'])\nprint('[PASS] existing Kalshi/sports pavement physically inventoried')\nprint('[PASS] no guessed dependency filename introduced')\nprint('[PASS] KSEM-002 certified')\n",encoding="utf-8")
    compile(TEST.read_text(encoding="utf-8"),str(TEST),"exec")
    print("[WRITE]",TEST.name)
    print("[PASS] execution_authority=FALSE")
if __name__=="__main__": main()
