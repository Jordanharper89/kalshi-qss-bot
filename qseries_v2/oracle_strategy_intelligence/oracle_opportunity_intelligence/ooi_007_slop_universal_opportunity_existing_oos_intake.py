from qseries_v2.oracle_intelligence.opportunity_operating_system.opportunity_operating_system import OpportunityOperatingSystem
from .ooi_006_slop_universal_opportunity_materializer import materialize_slop
REVISION="OOI_007_SLOP_UNIVERSAL_OPPORTUNITY_EXISTING_OOS_INTAKE"
EXECUTION_AUTHORITY=False
def intake_slop(op,system=None):
 u=materialize_slop(op)
 oos=system or OpportunityOperatingSystem()
 result=oos.intake(u)
 return u,result,oos
