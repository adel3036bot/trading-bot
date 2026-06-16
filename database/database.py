import sqlite3
from pathlib import Path


class DatabaseManager:

    def __init__(self):
        self.db_path = Path("adel_smart_bot.db")
        self.connection = sqlite3.connect(self.db_path)
        self.cursor = self.connection.cursor()

    def create_tables(self):

        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS signals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT,
            contract_type TEXT,
            strike REAL,
            expiry TEXT,
            entry_price REAL,
            tp1 REAL,
            tp2 REAL,
            tp3 REAL,
            stop_loss REAL,
            score INTEGER,
            signal_grade TEXT,
            status TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS updates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            signal_id INTEGER,
            update_type TEXT,
            profit_percent REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS daily_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            trade_date TEXT,
            total_signals INTEGER,
            wins INTEGER,
            losses INTEGER,
            win_rate REAL
        )
        """)

        self.connection.commit()

    def close(self):
        self.connection.close()


if __name__ == "__main__":

    db = DatabaseManager()

    db.create_tables()

    print("ADEL SMART BOT DATABASE CREATED")

    db.close()