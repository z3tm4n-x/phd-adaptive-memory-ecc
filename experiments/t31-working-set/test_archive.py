"""Offline safety checks; no Git or network writes."""
import copy
import unittest
from archive_branches import missing_tags, planned_tags


class ArchiveSafety(unittest.TestCase):
    def setUp(self):
        self.plan = {"base_sha": "a" * 40,
                     "excluded_active_branch": "refs/heads/t31-v22-working-set",
                     "branches": [{"branch": "refs/heads/main", "sha": "a" * 40,
                                   "tag": "refs/tags/v1/main"}]}

    def test_new_tags_only(self):
        self.assertEqual(len(missing_tags({}, planned_tags(self.plan))), 2)

    def test_identical_tags_are_skipped(self):
        wanted = planned_tags(self.plan)
        self.assertEqual(missing_tags(wanted, wanted), {})

    def test_conflicting_tag_stops(self):
        with self.assertRaises(ValueError):
            missing_tags({"refs/tags/v1/main": "b" * 40}, planned_tags(self.plan))

    def test_branch_cannot_be_destination(self):
        self.plan["branches"][0]["tag"] = "refs/heads/main"
        with self.assertRaises(ValueError):
            planned_tags(self.plan)

    def test_duplicate_target_stops(self):
        self.plan["branches"].append(copy.deepcopy(self.plan["branches"][0]))
        with self.assertRaises(ValueError):
            planned_tags(self.plan)

    def test_active_branch_excluded(self):
        self.plan["excluded_active_branch"] = "refs/heads/main"
        with self.assertRaises(ValueError):
            planned_tags(self.plan)


if __name__ == "__main__":
    unittest.main()
