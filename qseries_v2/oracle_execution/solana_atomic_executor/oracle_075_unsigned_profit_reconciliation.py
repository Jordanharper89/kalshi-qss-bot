"""ORACLE-075: independent unsigned balance/residue/fee truth.
Financial output is simulated, not realized; no signer or broadcaster here.
"""
import base64
import sys
import unittest

FEE_RESERVE_LAMPORTS = 100_000
MIN_PROFIT_LAMPORTS = 1


def _lamports(acct):
    if acct is None:
        return 0
    if not isinstance(acct, dict) or type(acct.get('lamports')) is not int:
        raise ValueError('ACCOUNT_LAMPORTS_UNAVAILABLE')
    return acct['lamports']


def _token_amount(acct):
    if acct is None:
        return 0
    data = acct.get('data')
    if not isinstance(data, (list, tuple)) or len(data) < 2 or data[1] != 'base64':
        raise ValueError('TOKEN_ACCOUNT_DATA_UNAVAILABLE')
    raw = base64.b64decode(data[0], validate=True)
    if len(raw) < 72:
        raise ValueError('TOKEN_ACCOUNT_DATA_TOO_SHORT')
    return int.from_bytes(raw[64:72], 'little')


def reconcile(pre, post, sim, start_lamports, fee_cap=FEE_RESERVE_LAMPORTS):
    """Ordering: user SOL, WSOL ATA, target token ATA. Reject partial visibility."""
    out = {'ok': False, 'sim_pass': False, 'estimated_net_lamports': None,
           'residue_verified': False, 'realized_profit_certified': False}
    if not isinstance(sim, dict) or sim.get('err') is not None:
        out['reason'] = 'SIM_ERROR'
        return out
    if type(sim.get('units')) is not int or sim['units'] <= 0:
        out['reason'] = 'SIM_UNITS_UNAVAILABLE'
        return out
    out['sim_pass'] = True
    if type(start_lamports) is not int or start_lamports < 10_000_000:
        out['reason'] = 'INVALID_EXECUTION_SIZE'
        return out
    if type(fee_cap) is not int or fee_cap < FEE_RESERVE_LAMPORTS:
        out['reason'] = 'FEE_CAP_BELOW_RESERVE'
        return out
    if not isinstance(pre, list) or not isinstance(post, list) or len(pre) != 3 or len(post) != 3:
        out['reason'] = 'INCOMPLETE_OWNER_ACCOUNT_VISIBILITY'
        return out
    try:
        if pre[0] is None or post[0] is None:
            raise ValueError('WALLET_ACCOUNT_UNAVAILABLE')
        if _lamports(pre[0]) < start_lamports + fee_cap:
            out['reason'] = 'INSUFFICIENT_WALLET_FOR_SIZE_AND_FEE_RESERVE'
            return out
        pre_token = _token_amount(pre[2])
        post_token = _token_amount(post[2])
        if pre_token != post_token:
            out['reason'] = 'TOKEN_RESIDUE_MISMATCH'
            out['residue_delta_raw'] = post_token - pre_token
            return out
        delta = sum(_lamports(x) for x in post) - sum(_lamports(x) for x in pre)
        net = delta - fee_cap
        out.update({'residue_verified': True, 'estimated_net_lamports': net,
                    'fee_reserve_lamports': fee_cap,
                    'gross_simulated_delta_lamports': delta})
        if net < MIN_PROFIT_LAMPORTS:
            out['reason'] = 'NO_POSITIVE_SIMULATED_FEE_ADJUSTED_NET'
            return out
        out['ok'] = True
        out['reason'] = 'POSITIVE_UNSIGNED_ESTIMATE_NOT_REALIZED'
        return out
    except (ValueError, TypeError, OverflowError, KeyError) as exc:
        out['reason'] = str(exc)[:80]
        return out


class Tests(unittest.TestCase):
    @staticmethod
    def token(value):
        buf = bytearray(165)
        buf[64:72] = int(value).to_bytes(8, 'little')
        return {'lamports': 2_039_280, 'data': [base64.b64encode(buf).decode(), 'base64']}

    def test_simulated_profit_not_realized(self):
        a = [{'lamports': 100_000_000}, {'lamports': 2_039_280}, self.token(0)]
        b = [{'lamports': 101_000_000}, {'lamports': 2_039_280}, self.token(0)]
        x = reconcile(a, b, {'err': None, 'units': 150000}, 10_000_000)
        self.assertTrue(x['ok'])
        self.assertFalse(x['realized_profit_certified'])
        self.assertEqual(x['estimated_net_lamports'], 900000)

    def test_residue_rejection(self):
        a = [{'lamports': 100_000_000}, None, self.token(0)]
        b = [{'lamports': 101_000_000}, None, self.token(9)]
        self.assertEqual(reconcile(a, b, {'err': None, 'units': 1}, 10_000_000)['reason'],
                         'TOKEN_RESIDUE_MISMATCH')

    def test_sim_error_rejection(self):
        self.assertEqual(reconcile([], [], {'err': 'fail'}, 10_000_000)['reason'], 'SIM_ERROR')

    def test_missing_balance_rejection(self):
        self.assertEqual(reconcile([], [], {'err': None, 'units': 10}, 10_000_000)['reason'],
                         'INCOMPLETE_OWNER_ACCOUNT_VISIBILITY')


if __name__ == '__main__':
    if '--test' in sys.argv:
        unittest.main(argv=[sys.argv[0]], verbosity=2)
    else:
        print('[PASS] ORACLE075_READY SIMULATED_PROFIT_NOT_REALIZED')
        print('[BOUNDARY] NO_RPC_NO_SIGNING_NO_BROADCAST')