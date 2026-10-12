import unittest
from config_check import InterfaceModel, expected_fields, proof_copy, vectors


class ConfigurationModelTests(unittest.TestCase):
    def ready(self):
        model = InterfaceModel(19, 174763)
        for address, value in enumerate(expected_fields(19)):
            model.step(1, 0, 1, address, value)
        return model

    def test_missing_and_wrong_field(self):
        model = self.ready()
        del model.values[11]
        self.assertEqual(model.outputs(0, 0, 1), 0)
        model.step(1, 0, 1, 11, 104)
        self.assertEqual(model.outputs(0, 0, 1), 8)
        model.step(1, 0, 1, 2, 32)
        self.assertEqual(model.outputs(0, 0, 1), 0)

    def test_wr_commit_is_no_write_and_no_arm(self):
        model = self.ready()
        self.assertEqual(model.step(1, 1, 1, 2, 0), (8, 12))
        self.assertEqual(model.values[2], 38)
        self.assertFalse(model.locked)

    def test_fault_is_sticky_but_not_a_new_arm_veto(self):
        model = self.ready()
        self.assertEqual(model.step(0, 1, 0, 0, 0), (8, 12))
        self.assertEqual(model.step(0, 1, 1, 0, 0), (13, 14))

    def test_lock_preserves_last_bank(self):
        model = self.ready()
        self.assertEqual(model.step(0, 1, 1, 0, 0), (9, 10))
        self.assertEqual(model.step(1, 0, 1, 0, 0), (10, 14))
        self.assertEqual(model.step(0, 1, 1, 0, 0), (14, 14))
        self.assertEqual(model.values, dict(enumerate(expected_fields(19))))

    def test_invalid_static_parameters_never_arm(self):
        for bits, inverse in ((2, 3), (20, 699051), (19, 1)):
            model = InterfaceModel(bits, inverse)
            for address, value in enumerate(expected_fields(bits)):
                model.step(1, 0, 1, address, value)
            self.assertEqual(model.step(0, 1, 1, 0, 0), (0, 4))

    def test_reproducible_vectors_and_closed_instrumentation(self):
        text, count = vectors(19, 174763)
        self.assertEqual((text, count), vectors(19, 174763))
        self.assertEqual(count, 1582)
        with self.assertRaises(ValueError):
            proof_copy("module drifted; endmodule", False)


if __name__ == "__main__":
    unittest.main()
