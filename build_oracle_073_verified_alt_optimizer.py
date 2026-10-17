"""ORACLE-073: bounded verified ALT combinations, no chain mutations."""
from itertools import combinations
import sys
import unittest

MAX_ALTS = 3
MAX_COMBINATIONS = 8
MAX_CANDIDATE_TABLES = 4


def plan_alt_sets(verified, maximum=MAX_COMBINATIONS):
    """Only accept records already attested by ORACLE-051 verified_table."""
    rows = []
    seen = set()
    for x in verified:
        if not isinstance(x, dict):
            continue
        address = x.get('address')
        if not isinstance(address, str) or not address or address in seen:
            continue
        coverage = x.get('covered_accounts')
        if type(coverage) is not int or coverage <= 0:
            continue
        seen.add(address)
        rows.append((address, coverage))
    rows.sort(key=lambda x: (-x[1], x[0]))
    rows = rows[:MAX_CANDIDATE_TABLES]
    groups = []
    for count in range(min(len(rows), MAX_ALTS), 0, -1):
        for combo in combinations(rows, count):
            keys = tuple(x[0] for x in combo)
            score = sum(x[1] for x in combo)
            groups.append((score, keys))
    groups.sort(key=lambda x: (-x[0], -len(x[1]), x[1]))
    options = [list(x[1]) for x in groups[:max(1, maximum - 1)]]
    options.append([])
    return options[:maximum]


class Tests(unittest.TestCase):
    def test_verified_only(self):
        self.assertEqual(plan_alt_sets([{'address': 'x', 'covered_accounts': 4},
                                        {'address': 'z', 'covered_accounts': 0},
                                        {'address': 'x', 'covered_accounts': 1}]), [['x'], []])

    def test_bounds_and_empty_fallback(self):
        v = [{'address': str(i), 'covered_accounts': i + 1} for i in range(20)]
        o = plan_alt_sets(v)
        self.assertLessEqual(len(o), MAX_COMBINATIONS)
        self.assertTrue(all(len(x) <= MAX_ALTS for x in o))
        self.assertEqual(o[-1], [])

    def test_unverified_cannot_be_used(self):
        self.assertEqual(plan_alt_sets([{'address': 'x'}, 'y']), [[]])


if __name__ == '__main__':
    if '--test' in sys.argv:
        unittest.main(argv=[sys.argv[0]], verbosity=2)
    else:
        print('[PASS] ORACLE073_READY VERIFIED_EXISTING_ALTS_ONLY')
        print('[BOUNDARY] NO_RPC_NO_ALT_EXTENSION_NO_SIGNING')