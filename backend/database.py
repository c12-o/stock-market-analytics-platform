"""
Database layer. Uses DATABASE_URL env var if present (e.g. a Postgres URL from
Render/Supabase/Railway); otherwise falls back to a local SQLite file so the
app runs with zero setup.
"""
import os
import time
import json
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./stock_cache.db")

# Render/Heroku-style URLs sometimes start with postgres:// — SQLAlchemy needs postgresql://
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)


def init_db():
    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS stock_cache (
                ticker TEXT NOT NULL,
                period TEXT NOT NULL,
                interval TEXT NOT NULL,
                data TEXT NOT NULL,
                fetched_at INTEGER NOT NULL,
                PRIMARY KEY (ticker, period, interval)
            )
        """))


def get_cached(ticker: str, period: str, interval: str, max_age_seconds: int = 900):
    with engine.begin() as conn:
        row = conn.execute(
            text("""SELECT data, fetched_at FROM stock_cache
                     WHERE ticker = :t AND period = :p AND interval = :i"""),
            {"t": ticker, "p": period, "i": interval}
        ).fetchone()
    if not row:
        return None
    data, fetched_at = row
    if time.time() - fetched_at > max_age_seconds:
        return None
    return json.loads(data)


def set_cached(ticker: str, period: str, interval: str, data: list):
    payload = json.dumps(data)
    now = int(time.time())
    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO stock_cache (ticker, period, interval, data, fetched_at)
            VALUES (:t, :p, :i, :d, :f)
            ON CONFLICT (ticker, period, interval)
            DO UPDATE SET data = excluded.data, fetched_at = excluded.fetched_at
        """), {"t": ticker, "p": period, "i": interval, "d": payload, "f": now})
