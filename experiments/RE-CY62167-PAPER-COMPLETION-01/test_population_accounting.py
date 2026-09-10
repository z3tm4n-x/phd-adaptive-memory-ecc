import os
import unittest
from pathlib import Path

from event_partition import load_archive, population_audit, aggregate_population, verify_frozen_addresses, grouped_events

class TestPopulationAccounting(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        raw = os.environ.get('CY62167_RAW_ARCHIVE')
        if not raw:
            raise RuntimeError('set CY62167_RAW_ARCHIVE to the controlled archive')
        cls.parsed = load_archive(Path(raw))
        cls.audit = population_audit(cls.parsed)
        cls.pop = aggregate_population(cls.audit)

    def test_counts(self):
        self.assertEqual(self.pop['RAW'], {'clusters':173835,'cells':299154})
        self.assertEqual(self.pop['ORDINARY'], {'clusters':173802,'cells':299121})
        self.assertEqual(self.pop['DEDUP'], {'clusters':173802,'cells':299026})
        self.assertEqual(self.pop['service_records'],15)
        self.assertEqual(self.pop['ambiguous_records'],18)
        self.assertEqual(self.pop['event_local_duplicate_cells'],95)
        self.assertEqual(self.pop['P_HI'], {'series':9,'clusters':8240,'cells':91284})

    def test_article_global_cell_count_is_discrepant(self):
        self.assertNotIn(299206, [self.pop['RAW']['cells'], self.pop['ORDINARY']['cells'], self.pop['DEDUP']['cells']])
        self.assertGreater(299206, self.pop['RAW']['cells'])

    def test_frozen_mapping_without_refit(self):
        checked, mismatches = verify_frozen_addresses(self.parsed)
        self.assertEqual(checked,148731)
        self.assertEqual(mismatches,[])

    def test_file_order_independence(self):
        forward = grouped_events(self.parsed)
        reverse = grouped_events(dict(reversed(list(self.parsed.items()))))
        self.assertEqual(list(forward), list(reverse))
        self.assertEqual(sum(map(len,forward.values())), sum(map(len,reverse.values())))

if __name__=='__main__': unittest.main()
