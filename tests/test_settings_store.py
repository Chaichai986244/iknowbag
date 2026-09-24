import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

import config_data as cfg
import database as db_module
from settings_store import get_settings, save_settings


class SettingsStoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = db_module.Database(os.path.join(self.tmp.name, "test.db"))

    def tearDown(self):
        self.tmp.cleanup()

    def test_reads_defaults_when_database_is_empty(self):
        settings = get_settings(db=self.db)

        self.assertEqual(settings["chunk_size"], cfg.chunk_size)
        self.assertEqual(settings["chunk_overlap"], cfg.chunk_overlap)
        self.assertEqual(settings["max_split"], cfg.max_split)
        self.assertEqual(settings["top_k"], cfg.top_k)
        self.assertEqual(settings["separators"], cfg.separators)

    def test_saves_valid_settings_and_updates_config_module(self):
        payload = {
            "chunk_size": 800,
            "chunk_overlap": 80,
            "max_split": 600,
            "top_k": 6,
            "separators": ["\\n\\n", "\\n", " ", "\\t"],
        }
        settings = save_settings(payload, db=self.db)
        loaded = get_settings(db=self.db)

        self.assertEqual(settings, loaded)
        self.assertEqual(settings["chunk_size"], 800)
        self.assertEqual(cfg.chunk_size, 800)
        self.assertEqual(cfg.chunk_overlap, 80)
        self.assertEqual(cfg.max_split, 600)
        self.assertEqual(cfg.top_k, 6)
        self.assertEqual(cfg.separators, ["\n\n", "\n", " ", "\t"])

    def test_rejects_overlap_that_is_not_smaller_than_chunk_size(self):
        with self.assertRaisesRegex(ValueError, "重叠长度必须小于分块长度"):
            save_settings({
                "chunk_size": 500,
                "chunk_overlap": 500,
                "max_split": 600,
                "top_k": 5,
                "separators": ["\\n"],
            }, db=self.db)

    def test_rejects_empty_separators(self):
        with self.assertRaisesRegex(ValueError, "至少保留一个分隔符"):
            save_settings({
                "chunk_size": 500,
                "chunk_overlap": 50,
                "max_split": 600,
                "top_k": 5,
                "separators": [],
            }, db=self.db)


if __name__ == "__main__":
    unittest.main()
