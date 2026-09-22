
from qseries_v2.oracle_source_network.certification.sports_event_extraction_truth_v2 import rows

def production_admission():
    truth=rows()
    admitted=tuple(x.league for x in truth if x.admitted and x.state=="PHYSICAL_EXTRACTING")
    held=tuple(x.league for x in truth if not x.admitted and x.state!="BLOCKED")
    blocked=tuple(x.league for x in truth if x.state=="BLOCKED")
    return {
        "passed": admitted==("NFL","NCAAF","NBA"),
        "admitted":admitted,
        "held":held,
        "blocked":blocked,
        "execution_authority":False,
    }
