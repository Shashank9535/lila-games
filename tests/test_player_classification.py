import unittest

from data_pipeline.processor import classify_player


class PlayerClassificationTests(unittest.TestCase):
    def test_uuid_is_human(self):
        self.assertEqual(classify_player("0019c582-574d-4a53-9f77-554519b75b4c"), "human")

    def test_numeric_id_is_bot(self):
        self.assertEqual(classify_player("1440"), "bot")

    def test_other_ids_are_not_invented_as_a_class(self):
        self.assertEqual(classify_player("player-1440"), "ambiguous")


if __name__ == "__main__":
    unittest.main()
