"""Sentinels against treating an incomplete solver run as a proof."""
import unittest
from pdr_check import classify


class ProofResultTests(unittest.TestCase):
    HEADER = "aig 450 13 105 0 332 5 0 0 0"
    TOTALS = "Properties: All = 5. Proved = 5. Disproved = 0. Undecided = 0."
    VALID = "Verification of invariant with 1549 clauses was successful.\n"

    def test_complete_and_validated(self):
        self.assertEqual(classify(self.HEADER, self.VALID+self.TOTALS, 5, 0)["status"], "proved")

    def test_zero_exit_is_not_proof(self):
        for log in ("", self.TOTALS, self.VALID+self.TOTALS+self.TOTALS):
            self.assertEqual(classify(self.HEADER, log, 5, 0)["status"], "inconclusive")

    def test_partial_or_timeout_not_proof(self):
        log = self.VALID+"Properties: All = 5. Proved = 4. Disproved = 0. Undecided = 1."
        self.assertEqual(classify(self.HEADER, log, 5, 0)["status"], "inconclusive")
        self.assertEqual(classify(self.HEADER, self.VALID+self.TOTALS, 5, 1)["status"], "inconclusive")

    def test_counterexample_is_not_timeout(self):
        log = "Properties: All = 5. Proved = 4. Disproved = 1. Undecided = 0."
        self.assertEqual(classify(self.HEADER, log, 5, 0)["status"], "disproved")

    def test_constraints_vacuity_and_wrong_totals_rejected(self):
        for header in (self.HEADER.replace("5 0 0 0", "5 1 0 0"), self.HEADER.replace("332 5", "332 0")):
            with self.assertRaises(ValueError):
                classify(header, self.VALID+self.TOTALS, 5, 0)
        with self.assertRaises(ValueError):
            classify(self.HEADER, self.TOTALS.replace("Proved = 5", "Proved = 4"), 5, 0)


if __name__ == "__main__":
    unittest.main()
