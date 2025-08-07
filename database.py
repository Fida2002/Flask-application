import sqlite3
import datetime
from typing import List, Dict, Optional, Tuple
import os

class DatabaseManager:
    def __init__(self, db_path: str = 'watchlist.db'):
        """Initialize database manager with specified database path"""
        self.db_path = db_path
        
    def init_db(self) -> None:
        """Initialize the database with required tables"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS watchlist (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ticker TEXT UNIQUE NOT NULL,
                    asset_type TEXT NOT NULL,
                    added_at TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()
    
    def add_stock_to_watchlist(self, ticker: str, asset_type: str) -> bool:
        """Add a ticker to the watchlist"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT OR REPLACE INTO watchlist (ticker, asset_type, added_at) VALUES (?, ?, ?)",
                    (ticker.upper(), asset_type, datetime.datetime.now().isoformat())
                )
                conn.commit()
                return True
        except sqlite3.Error as e:
            print(f"Error adding stock to database: {e}")
            return False
    
    def remove_stock_from_watchlist(self, ticker: str) -> bool:
        """Remove a ticker from the watchlist"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM watchlist WHERE ticker = ?", (ticker.upper(),))
                conn.commit()
                return cursor.rowcount > 0
        except sqlite3.Error as e:
            print(f"Error removing stock from database: {e}")
            return False
    
    def get_watchlist(self) -> List[Dict[str, str]]:
        """Retrieve all tickers from the watchlist"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT ticker, asset_type, added_at FROM watchlist ORDER BY added_at DESC")
                rows = cursor.fetchall()
                return [
                    {
                        'ticker': row[0],
                        'asset_type': row[1],
                        'added_at': row[2]
                    }
                    for row in rows
                ]
        except sqlite3.Error as e:
            print(f"Error retrieving watchlist: {e}")
            return []
    
    def get_ticker_info(self, ticker: str) -> Optional[Dict[str, str]]:
        """Get information for a specific ticker"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT ticker, asset_type, added_at FROM watchlist WHERE ticker = ?",
                    (ticker.upper(),)
                )
                row = cursor.fetchone()
                if row:
                    return {
                        'ticker': row[0],
                        'asset_type': row[1],
                        'added_at': row[2]
                    }
                return None
        except sqlite3.Error as e:
            print(f"Error getting ticker info: {e}")
            return None
    
    def clear_watchlist(self) -> bool:
        """Clear all tickers from the watchlist"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM watchlist")
                conn.commit()
                return True
        except sqlite3.Error as e:
            print(f"Error clearing watchlist: {e}")
            return False
    
    def get_watchlist_count(self) -> int:
        """Get the number of tickers in the watchlist"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM watchlist")
                return cursor.fetchone()[0]
        except sqlite3.Error as e:
            print(f"Error getting watchlist count: {e}")
            return 0