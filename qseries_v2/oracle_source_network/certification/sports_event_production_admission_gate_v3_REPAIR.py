
import json
from pathlib import Path

REPORT=Path("qseries_v2/oracle_source_network/certification/osn_054_remaining_sports_surface_report_REPAIR.json")

BASE_ADMITTED=("NFL","NCAAF","NBA")

def admission():
    if not REPORT.exists():
        raise RuntimeError("repaired OSN-054 physical report missing")

    r=json.loads(REPORT.read_text(encoding="utf-8"))
    by={x["league"]:x for x in r.get("rows",[])}

    admitted=list(BASE_ADMITTED)
    for league in ("NHL","MLS","EPL"):
        row=by.get(league,{})
        if row.get("passed") is True and row.get("kind")=="EXTRACTOR":
            admitted.append(league)

    held=("NCAAB",)
    blocked=("UCL",)

    return {
        "passed": (
            r.get("passed") is True
            and tuple(admitted)==("NFL","NCAAF","NBA","NHL","MLS","EPL")
        ),
        "admitted":tuple(admitted),
        "held":held,
        "blocked":blocked,
        "execution_authority":False,
    }
