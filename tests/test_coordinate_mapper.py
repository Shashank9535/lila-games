import unittest

from data_pipeline.coordinate_mapper import map_world_position


class CoordinateMapperTests(unittest.TestCase):
    def test_audit_examples(self):
        cases = [
            ("AmbroseValley", -315.3538818359375, -2.5926055908203125, 62.18, 488.78),
            ("GrandRift", -223.18521118164062, 42.54265594482422, 117.76, 437.90),
            ("Lockdown", -346.56146240234375, 132.7766876220703, 157.12, 376.04),
        ]
        for map_id, x, z, expected_x, expected_y in cases:
            with self.subTest(map_id=map_id):
                mapped = map_world_position(map_id, x, z)
                self.assertAlmostEqual(mapped["pixel_x"], expected_x, places=2)
                self.assertAlmostEqual(mapped["pixel_y"], expected_y, places=2)
                self.assertTrue(mapped["in_bounds"])

    def test_out_of_bounds_is_flagged(self):
        mapped = map_world_position("Lockdown", 501, -500)
        self.assertFalse(mapped["in_bounds"])
        self.assertGreater(mapped["u"], 1)

    def test_unknown_or_missing_map_is_rejected(self):
        with self.assertRaises(ValueError):
            map_world_position("Unknown", 0, 0)
        with self.assertRaises(ValueError):
            map_world_position(None, 0, 0)  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
