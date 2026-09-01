import sqlite3
from pathlib import Path
DB_PATH=Path(__file__).resolve().parent.parent/'data'/'revenueos.db'
def get_conn():
    c=sqlite3.connect(DB_PATH); c.row_factory=sqlite3.Row; return c
def init_db():
    DB_PATH.parent.mkdir(exist_ok=True); c=get_conn()
    c.executescript('''
    CREATE TABLE IF NOT EXISTS customers(id TEXT PRIMARY KEY,name TEXT,email TEXT,phone TEXT,tenure_months INTEGER,successful_payments INTEGER,previous_failures INTEGER,disputes INTEGER,preferred_method TEXT);
    CREATE TABLE IF NOT EXISTS transactions(id TEXT PRIMARY KEY,customer_id TEXT,amount INTEGER,currency TEXT,status TEXT,failure_code TEXT,description TEXT,created_at TEXT,retry_count INTEGER,recovered INTEGER);
    CREATE TABLE IF NOT EXISTS recovery_cases(id TEXT PRIMARY KEY,transaction_id TEXT,status TEXT,risk TEXT,confidence REAL,reason TEXT,action TEXT,amount INTEGER,created_at TEXT,updated_at TEXT,recovered_amount INTEGER DEFAULT 0);
    CREATE TABLE IF NOT EXISTS audit_logs(id INTEGER PRIMARY KEY AUTOINCREMENT,case_id TEXT,event_type TEXT,actor TEXT,message TEXT,metadata TEXT,created_at TEXT);
    CREATE TABLE IF NOT EXISTS knowledge(id INTEGER PRIMARY KEY AUTOINCREMENT,title TEXT,content TEXT,category TEXT);
    '''); c.commit(); c.close()
