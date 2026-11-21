import unittest

from data_pipeline.manifest import build_match_manifest
from data_pipeline.processor import filter_events, process_match_events


class TimestampProcessingTests(unittest.TestCase):
    def _event(self, timestamp_ms, x=1.0):
        return {
            "user_id": "1440",
            "match_id": "match-1.nakama-0",
            "map_id": "Lockdown",
            "x": x,
            "y": 0.0,
            "z": 2.0,
            "ts": "preserved-original-timestamp",
            "timestamp_ms": timestamp_ms,
            "event": b"BotPosition",
        }

    def test_sorting_and_relative_playback_are_timezone_independent(self):
        result = process_match_events([self._event(1_770_681_540), self._event(1_770_681_535)])
        self.assertEqual([event["timestamp_ms"] for event in result["events"]], [1_770_681_535, 1_770_681_540])
        self.assertEqual([event["relative_t_ms"] for event in result["events"]], [0, 5])
        self.assertEqual(result["timestamp_inversions"], 1)

    def test_duplicates_remain_present(self):
        event = self._event(100)
        result = process_match_events([event, event])
        self.assertEqual(len(result["events"]), 2)
        self.assertEqual(result["duplicate_count"], 1)

    def test_manifest_preserves_raw_parquet_millisecond_integer(self):
        # This is a real-scale source value, not a Unix-seconds value to convert.
        raw_timestamp_ms = 1_770_754_537
        event = self._event(raw_timestamp_ms)
        event["date_folder"] = "February_10"
        event["event_name"] = "BotPosition"
        manifest = build_match_manifest([event])[0]
        self.assertEqual(manifest["min_timestamp_raw_ms"], raw_timestamp_ms)
        self.assertEqual(manifest["max_timestamp_raw_ms"], raw_timestamp_ms)
        self.assertNotIn("min_timestamp_ms", manifest)

    def test_manifest_preserves_multiple_source_date_folders(self):
        first = self._event(100)
        first.update({"date_folder": "February_10", "event_name": "BotPosition"})
        second = self._event(105, x=2.0)
        second.update({"date_folder": "February_11", "event_name": "BotPosition"})
        manifest = build_match_manifest([first, second])[0]
        self.assertEqual(manifest["date_folders"], "February_10;February_11")
        self.assertEqual(manifest["first_date_folder"], "February_10")
        self.assertEqual(manifest["last_date_folder"], "February_11")

    def test_player_and_event_filters_keep_matching_source_rows(self):
        first = self._event(100)
        first.update({"event_name": "BotPosition", "player_class": "bot"})
        second = self._event(105, x=2.0)
        second.update({"user_id": "0019c582-574d-4a53-9f77-554519b75b4c", "event_name": "Loot", "player_class": "human"})
        result = filter_events([first, second], event_types={"Loot"}, player_id=second["user_id"])
        self.assertEqual(result, [second])


if __name__ == "__main__":
    unittest.main()
