"""MTR-151: bound simulation/economics revalidation; no transaction creation."""
import hashlib
from decimal import Decimal
from dataclasses import replace
from types import MappingProxyType
from qseries_v2.oracle_execution.solana_atomic_executor.mtr_147_protected_economics_gate import ProtectedEvidence, ProtectedCandidateGate

class BoundSimulationVerifier:
    """Pass only evidence independently checked by injected canonical inspectors.

    The inspectors MUST use real native instruction decoding and chain data;
    fixtures are only used by tests. Passing booleans from candidate data is
    never sufficient. This class does not call RPC, compile or sign.
    """
    def __init__(self, inspect_compiled=None, inspect_economics=None):
        self.inspect_compiled = inspect_compiled
        self.inspect_economics = inspect_economics
        self._bound = None

    def bind(self, compiled, simulation, evidence):
        self._bound = None
        if not isinstance(evidence, ProtectedEvidence):
            return False
        if not isinstance(compiled, dict) or not isinstance(simulation, dict):
            return False
        raw = compiled.get('raw')
        if type(raw) is not bytes or not raw:
            return False
        if simulation.get('err', 'MISSING') is not None:
            return False
        if type(simulation.get('units')) is not int or simulation['units'] <= 0:
            return False
        if not callable(self.inspect_compiled) or not callable(self.inspect_economics):
            return False
        try:
            tx = self.inspect_compiled(raw)
            econ = self.inspect_economics(raw, tx, simulation)
        except Exception:
            return False
        if not isinstance(tx, dict) or not isinstance(econ, dict):
            return False
        expected_tx = {'route_id': evidence.route_id,
                       'direction': evidence.direction,
                       'size_sol': evidence.size_sol,
                       'generation': evidence.generation,
                       'atomic_two_leg': True, 'pump_bounds': True,
                       'dlmm_bounds': True, 'unsigned_simulation_only': True}
        if any(tx.get(k) != v for k, v in expected_tx.items()):
            return False
        expected_econ = {
            'input_lamports': evidence.input_lamports,
            'minimum_final_lamports': evidence.minimum_final_lamports,
            'network_fee_lamports': evidence.network_fee_lamports,
            'priority_fee_lamports': evidence.priority_fee_lamports,
            'rent_and_residue_lamports': evidence.rent_and_residue_lamports}
        if any(type(econ.get(k)) is not int or econ[k] != v
               for k, v in expected_econ.items()):
            return False
        digest = hashlib.sha256(raw).hexdigest()
        if evidence.verifier_receipt != digest:
            return False
        self._bound = (evidence, digest)
        return True

    def __call__(self, evidence):
        return type(evidence) is ProtectedEvidence and self._bound is not None and self._bound == (evidence, evidence.verifier_receipt)

def evaluate_bound(compiled, simulation, evidence, *, route_id,
                   generation, inspect_compiled=None, inspect_economics=None):
    verifier = BoundSimulationVerifier(inspect_compiled, inspect_economics)
    if not verifier.bind(compiled, simulation, evidence):
        return MappingProxyType({'status': 'HOLD', 'reason': 'CANONICAL_EVIDENCE_NOT_BOUND'})
    return ProtectedCandidateGate(verifier).evaluate(
        evidence, expected_route=route_id, expected_generation=generation)

if __name__ == '__main__':
    print('[MTR151] VERIFIER_BINDING_ADAPTER_IMPORT_PASS')
    print('[NATIVE_INSPECTORS] NOT_CONNECTED')
    print('[SIMULATION_INVOKED] FALSE')
    print('[OFFICIAL_PROFIT_CERTIFIED] FALSE')
    print('[PRODUCTION_CUTOVER] FALSE')
    print('[PRIVATE_KEY] NOT_USED')
    print('[SIGNING] FALSE')
    print('[BROADCAST] FALSE')
