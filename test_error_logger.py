import unittest
import sqlite3
import os
from error_logger import ErrorLogger
from pathlib import Path

class TestErrorLogger(unittest.TestCase):
    def setUp(self):
        self.config = {}
        self.error_logger = ErrorLogger(self.config)
        self.db_path = self.error_logger.db_path

    def tearDown(self):
        # Clean up the database file
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_init_error_db(self):
        # Check if the database file is created
        self.assertTrue(os.path.exists(self.db_path))

        # Check if the error_logs table is created
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='error_logs'")
        table = c.fetchone()
        self.assertIsNotNone(table)
        conn.close()

    def test_log_to_db(self):
        error_type = "TEST"
        url = "http://example.com"
        message = "Test error message"
        details = "Test details"

        self.error_logger.log_to_db(error_type, url, message, details)

        # Verify that the error was logged to the database
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT * FROM error_logs WHERE error_type=? AND url=? AND message=? AND details=?",
                  (error_type, url, message, details))
        log = c.fetchone()
        self.assertIsNotNone(log)
        self.assertEqual(log[2], error_type)
        self.assertEqual(log[3], url)
        self.assertEqual(log[4], message)
        self.assertEqual(log[5], details)
        conn.close()

if __name__ == '__main__':
    unittest.main()