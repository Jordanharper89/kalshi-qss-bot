"""MTR-147 protected quote evidence gate; no production execution authority."""
from dataclasses import dataclass
from decimal import Decimal
from types import MappingProxyType

SIZES = (Decimal('0.010'), Decimal('0.015'), Decimal('0.020'), Decimal('0.025'), Decimal('0.030'))
DIRECTIONS = ('PUMP_TO_METEORA', 'METEORA_TO_PUMP')

@dataclass(frozen=True)
class ProtectedEvidence:
    route_id: str
    direction: str
    size_sol: Decimal
    generation: int
    input_lamports: int
    minimum_final_lamports: int
    network_fee_lamports: int
    priority_fee_lamports: int
    rent_and_residue_lamports: int
    pump_bounds_checked: bool
    dlmm_bounds_checked: bool
    atomic_two_leg_verified: bool
    verifier_receipt: str

class ProtectedCandidateGate:
    """Accept only externally verified official protected economics.

    The injected verifier MUST recompute provenance from trusted SDK/transaction
    artifacts, not trust the evidence's own claimed flags. No verifier => HOLD.
    """
    def __init__(self, trusted_verifier=None):
        self._verifier = trusted_verifier

    def evaluate(self, evidence, *, expected_route, expected_generation):
        if not isinstance(evidence, ProtectedEvidence):
            return MappingProxyType({'status':'HOLD', 'reason':'PROTECTED_EVIDENCE_REQUIRED'})
        e = evidence
        if e.route_id != expected_route or e.generation != expected_generation:
            return MappingProxyType({'status':'HOLD', 'reason':'ROUTE_OR_GENERATION_MISMATCH'})
        if e.direction not in DIRECTIONS or e.size_sol not in SIZES:
            return MappingProxyType({'status':'HOLD', 'reason':'SIZE_OR_DIRECTION_INVALID'})
        vals = (e.input_lamports, e.minimum_final_lamports,
                e.network_fee_lamports, e.priority_fee_lamports,
                e.rent_and_residue_lamports)
        if any(type(v) is not int or v < 0 for v in vals) or e.input_lamports == 0:
            return MappingProxyType({'status':'HOLD', 'reason':'INVALID_LAMPORT_ACCOUNTING'})
        if not (e.pump_bounds_checked and e.dlmm_bounds_checked and e.atomic_two_leg_verified):
            return MappingProxyType({'status':'HOLD', 'reason':'ATOMIC_PROTECTION_UNVERIFIED'})
        if not callable(self._verifier) or not e.verifier_receipt:
            return MappingProxyType({'status':'HOLD', 'reason':'TRUSTED_OFFICIAL_VERIFIER_MISSING'})
        # Verifier errors do not become profitable candidates.
        try:
            verified = self._verifier(e)
        except Exception:
            return MappingProxyType({'status':'HOLD', 'reason':'VERIFIER_ERROR'})
        if verified is not True:
            return MappingProxyType({'status':'HOLD', 'reason':'OFFICIAL_EVIDENCE_NOT_VERIFIED'})
        net = (e.minimum_final_lamports - e.input_lamports
               - e.network_fee_lamports - e.priority_fee_lamports
               - e.rent_and_residue_lamports)
        if net <= 0:
            return MappingProxyType({'status':'HOLD', 'reason':'NOT_PROTECTED_POSITIVE', 'net_lamports':net})
        bps = Decimal(net) * 10000 / Decimal(e.input_lamports)
        return MappingProxyType({'status':'REVALIDATION_CANDIDATE', 'route_id':e.route_id,
              'direction':e.direction, 'size_sol':str(e.size_sol),
              'generation':e.generation, 'net_lamports':net, 'bps':str(bps),
              'signing_authorized':False, 'broadcast_authorized':False})

def main():
    gate = ProtectedCandidateGate()
    result = gate.evaluate({'local_bps':10000, 'local_net':100000000},
                           expected_route='example', expected_generation=1)
    print('[MTR147_INDICATIVE_ONLY]', result['reason'])
    print('[OFFICIAL_VERIFIER_CONNECTED] FALSE')
    print('[PROTECTED_PROFIT_CERTIFIED] FALSE')
    print('[PRODUCTION_CUTOVER] FALSE')
    print('[CANONICAL_SCANNER] FROZEN')
    print('[PRIVATE_KEY] NOT_USED')
    print('[SIGNING] FALSE')
    print('[BROADCAST] FALSE')

if __name__ == '__main__':
    main()
