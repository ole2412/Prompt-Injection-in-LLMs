import asyncio
import os
import random
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional


class SQLiteConnection:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row

        
    def __enter__(self):
        return self.conn
    
    def setup_table(self, emails):
        cur = self.conn.cursor()
        
        # create table if it does not exist
        if "users" not in str(cur.execute("""SELECT name FROM sqlite_schema
        WHERE type='table'
        ORDER BY name;""").fetchall()):
            cur.execute("""CREATE TABLE users (
                            user_id INTEGER NOT NULL,                          
                            email VARCHAR(255) NOT NULL,              
                            order_quantity INTEGER DEFAULT 0               
                        );"""
                        )
            
        # insert data if table is empty
        if not cur.execute("SELECT email FROM users LIMIT 1;").fetchall():            
            for i, email in enumerate(emails):
                value = random.randint(0, 200)
                cur.execute("""
                    INSERT INTO users (user_id, email, order_quantity) VALUES (?, ?, ?)
                """, (i, email, value))
        self.conn.commit()
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.conn:
            self.conn.close()