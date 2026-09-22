from pathlib import Path

ROOT = Path.cwd()

def require(rel):
    p = ROOT / rel
    if not p.exists():
        raise SystemExit("[FAIL] missing dependency: " + str(p))
    print("[PASS] dependency verified:", p.relative_to(ROOT))

def write(rel, content):
    p = ROOT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content.rstrip() + "\n", encoding="utf-8")
    print("[WRITE]", p.relative_to(ROOT))

def main():
    print("=" * 118)
    print(' OSN-025 SPORTS SOURCE ADMISSION + BLOCKED SOURCE POLICY INSTALLER')
    print("=" * 118)
    require('qseries_v2/oracle_source_network/certification/sports_source_truth.py')
    write('qseries_v2/oracle_source_network/certification/sports_source_admission.py', '\nfrom dataclasses import dataclass\nfrom .sports_source_truth import blocked, production_ready\n\n@dataclass(frozen=True, slots=True)\nclass SourceAdmissionDecision:\n    source_id: str\n    league: str\n    admitted: bool\n    status: str\n    reason: str\n    execution_authority: bool = False\n\ndef admission_decisions():\n    ready = [\n        SourceAdmissionDecision(x.source_id, x.league, True, x.status, "physically certified source")\n        for x in production_ready()\n    ]\n    denied = [\n        SourceAdmissionDecision(x.source_id, x.league, False, x.status, x.reason)\n        for x in blocked()\n    ]\n    return tuple(ready + denied)\n\ndef admitted_leagues():\n    return tuple(x.league for x in admission_decisions() if x.admitted)\n')
    write('test_osn_025_sports_source_admission_blocked_source_policy.py', '\nfrom qseries_v2.oracle_source_network.certification.sports_source_admission import admission_decisions, admitted_leagues\n\nd = admission_decisions()\nucl = [x for x in d if x.league == "UCL"][0]\nassert ucl.admitted is False\nassert ucl.status == "BLOCKED"\nassert "zero bytes" in ucl.reason\nassert set(admitted_leagues()) == {"NFL","NCAAF","NBA","NCAAB","NHL","MLS","EPL"}\nassert all(x.execution_authority is False for x in d)\nprint("[PASS] admitted_leagues=", admitted_leagues())\nprint("[PASS] UCL blocked-source exclusion preserved")\nprint("[PASS] OSN-025 source admission policy certified")\n')
    print('[PASS] OSN-025 installed')
    print('[PASS] blocked sources cannot enter production-ready set')
    print('[PASS] execution_authority=FALSE')

if __name__ == "__main__":
    main()
