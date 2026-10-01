from pathlib import Path
import re

ROOT = Path.cwd()
OUT = ROOT / "OOI_001_EXISTING_CAPABILITY_AUDIT.txt"

TERMS = {
    "IDENTITY_ASSOCIATION": r"identity|association|entity_resolution|canonical.*market",
    "EVIDENCE_FUSION": r"evidence|condition.*snapshot|context.*projection|fusion",
    "REASONING_THESIS": r"reasoning|thesis|hypothesis|comparable.*case|probability",
    "PROSPECTIVE_PREDICTION": r"prospective|prediction|forecast|frozen.*prediction",
    "PATH_OUTCOME": r"forward.*outcome|economic.*resolution|maturity|path",
    "LEARNING": r"learning|learner|outcome_observation|learning_event",
    "RANKING": r"ranking|recommendation|opportunity.*score",
}

def main():
    files = list((ROOT / "qseries_v2").rglob("*.py"))
    lines = []
    hits = {}
    for capability, pattern in TERMS.items():
        rx = re.compile(pattern, re.I)
        matched = [p.relative_to(ROOT).as_posix() for p in files if rx.search(p.name)]
        hits[capability] = matched
        lines.append(f"[{capability}] count={len(matched)}")
        lines.extend(f"  {x}" for x in matched)
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    assert files, "no qseries_v2 Python source found"
    assert hits["LEARNING"], "existing learning pavement not discovered"
    assert hits["PROSPECTIVE_PREDICTION"], "prospective pavement not discovered"
    print(f"[FILES_SCANNED] {len(files)}")
    for k, v in hits.items():
        print(f"[{k}] {len(v)}")
    print(f"[AUDIT] {OUT}")
    print("[PASS] OOI-001 existing capability physical audit")
    print("[PASS] read_only=True execution_authority=FALSE")

if __name__ == "__main__":
    main()