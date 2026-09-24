import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from langchain_core.messages import HumanMessage

import database as db_module
from file_history_store import FileChatMessageHistory, delete_history, list_histories


class DeleteHistoryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = db_module.Database(os.path.join(self.tmp.name, "test.db"))

    def tearDown(self):
        self.tmp.cleanup()

    def test_deletes_existing_history(self):
        history = FileChatMessageHistory("session-a", db=self.db)
        history.add_messages([HumanMessage(content="你好")])

        self.assertTrue(delete_history("session-a", db=self.db))
        self.assertEqual(history.messages, [])

    def test_missing_history_returns_false(self):
        self.assertFalse(delete_history("missing", db=self.db))

    def test_add_messages_stores_created_at_timestamp(self):
        history = FileChatMessageHistory("session-a", db=self.db)
        history.add_messages([HumanMessage(content="你好")])

        messages = history.messages

        self.assertEqual(len(messages), 1)
        self.assertRegex(
            messages[0].additional_kwargs["created_at"],
            r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$",
        )

    def test_list_histories_returns_session_summary(self):
        history = FileChatMessageHistory("sess-1", db=self.db)
        history.add_messages([HumanMessage(content="第一个问题")])
        history.add_messages([HumanMessage(content="第二个问题")])

        items = list_histories(db=self.db)

        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["session_id"], "sess-1")
        self.assertEqual(items[0]["title"], "第一个问题")
        self.assertEqual(items[0]["message_count"], 2)


if __name__ == "__main__":
    unittest.main()
