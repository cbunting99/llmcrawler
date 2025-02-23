import sqlite3
import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

class ErrorLogger:
    def __init__(self, config):
        self.config = config
        self.db_path = Path('crawler_errors.db')
        self._init_error_db()

    def _init_error_db(self):
        try:
            conn = sqlite3.connect(str(self.db_path))
            c = conn.cursor()
            c.execute("""
                CREATE TABLE IF NOT EXISTS error_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    error_type TEXT NOT NULL,
                    url TEXT,
                    message TEXT NOT NULL,
                    details TEXT
                )
            """)
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")

    def log_to_db(self, error_type, url, message, details=None):
        try:
            conn = sqlite3.connect(str(self.db_path))
            c = conn.cursor()
            c.execute("""
                INSERT INTO error_logs (timestamp, error_type, url, message, details)
                VALUES (?, ?, ?, ?, ?)
            """, (
                datetime.now().isoformat(),
                error_type,
                url,
                message,
                details
            ))
            conn.commit()
        except Exception as e:
            logger.error(f"Failed to log to database: {e}")
        finally:
            if 'conn' in locals():
                conn.close()