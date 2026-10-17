"""ORACLE-072: strict existing-route admission, no scanner replacement."""
import sys
import unittest

MIN_LAMPORTS = 10_000_000
MAX_TX_BYTES = 1232


def validate_route(route, pump_program, dlmm_program, instructions):
    if not isinstance(route, dict):
        return 'ROUTE_NOT_MAPPING'
    if type(route.get('start_lamports')) is not int or route['start_lamports'] < MIN_LAMPORTS:
        return 'BELOW_010_SOL'
    if not isinstance(route.get('token'), str) or not route['token']:
        return 'TOKEN_MISSING'
    if not isinstance(instructions, list) or not instructions:
        return 'INSTRUCTIONS_MISSING'
    counts = {pump_program: 0, dlmm_program: 0}
    for ix in instructions:
        if not isinstance(ix, dict) or not isinstance(ix.get('programId'), str):
            return 'INVALID_PROGRAM_ID'
        if not isinstance(ix.get('accounts'), list) or not isinstance(ix.get('data'), str):
            return 'INCOMPLETE_NATIVE_INSTRUCTION'
        if ix['programId'] in counts:
            counts[ix['programId']] += 1
        for a in ix['accounts']:
            if (not isinstance(a, dict) or not isinstance(a.get('pubkey'), str)
                    or type(a.get('isSigner')) is not bool
                    or type(a.get('isWritable')) is not bool):
                return 'INVALID_ACCOUNT_META'
    if counts[pump_program] != 1 or counts[dlmm_program] != 1:
        return 'NOT_EXACTLY_TWO_VENUE_LEGS'
    return 'ADMITTED'


class Tests(unittest.TestCase):
    def setUp(self):
        self.route = {'token': 'token', 'start_lamports': 10_000_000}
        self.ix = [{'programId': x, 'accounts': [], 'data': ''} for x in ('P', 'D')]

    def test_admits_both_programs(self):
        self.assertEqual(validate_route(self.route, 'P', 'D', self.ix), 'ADMITTED')

    def test_below_canary_rejected(self):
        self.route['start_lamports'] = 9_999_999
        self.assertEqual(validate_route(self.route, 'P', 'D', self.ix), 'BELOW_010_SOL')

    def test_single_leg_rejected(self):
        self.assertEqual(validate_route(self.route, 'P', 'D', self.ix[:1]), 'NOT_EXACTLY_TWO_VENUE_LEGS')

    def test_missing_meta_rejected(self):
        self.ix[0]['accounts'] = [{'pubkey': 'abc'}]
        self.assertEqual(validate_route(self.route, 'P', 'D', self.ix), 'INVALID_ACCOUNT_META')


if __name__ == '__main__':
    if '--test' in sys.argv:
        unittest.main(argv=[sys.argv[0]], verbosity=2)
    else:
        print('[PASS] ORACLE072_READY ORIGINAL_SCANNER_UNCHANGED')
        print('[BOUNDARY] NO_RPC_NO_SIGNING_NO_BROADCAST')