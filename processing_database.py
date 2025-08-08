#!/usr/bin/env python3
"""
Processing Database
-------------------
SQLite-backed storage for processed email records and aggregation utilities.
"""

import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta
from typing import Any, Dict, List

DATA_DIR = os.path.join(os.getcwd(), 'data')
DB_PATH = os.path.join(DATA_DIR, 'processing.db')


def _ensure_db():
    os.makedirs(DATA_DIR, exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS processed_emails (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                subject TEXT,
                sender TEXT,
                category TEXT,
                confidence REAL,
                sentiment TEXT,
                processing_time REAL,
                content_length INTEGER,
                api_cost_openai REAL,
                api_cost_huggingface REAL
            )
            """
        )
        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_processed_emails_timestamp
            ON processed_emails(timestamp)
            """
        )
        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_processed_emails_category
            ON processed_emails(category)
            """
        )
        conn.commit()


@contextmanager
def _get_conn():
    _ensure_db()
    conn = sqlite3.connect(DB_PATH)
    try:
        yield conn
    finally:
        conn.close()


def record_processed_email(
    subject: str,
    sender: str,
    category: str,
    confidence: float = None,
    sentiment: str = None,
    processing_time: float = None,
    content_length: int = None,
    api_costs: Dict[str, float] | None = None,
) -> None:
    """Insert a processed email record."""
    ts = datetime.utcnow().isoformat()
    api_costs = api_costs or {}
    with _get_conn() as conn:
        conn.execute(
            """
            INSERT INTO processed_emails (
                timestamp, subject, sender, category, confidence, sentiment, processing_time,
                content_length, api_cost_openai, api_cost_huggingface
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                ts,
                subject or '',
                sender or '',
                category or 'General Inquiries',
                float(confidence) if confidence is not None else None,
                (sentiment or '').upper() if sentiment else None,
                float(processing_time) if processing_time is not None else None,
                int(content_length) if content_length is not None else None,
                float(api_costs.get('openai', 0.0)),
                float(api_costs.get('huggingface', 0.0)),
            ),
        )
        conn.commit()


def _rows_to_dicts(cursor, rows) -> List[Dict[str, Any]]:
    cols = [d[0] for d in cursor.description]
    return [dict(zip(cols, r)) for r in rows]


def get_processing_statistics(days: int = 30) -> Dict[str, Any]:
    """Aggregate stats over the last N days."""
    since = (datetime.utcnow() - timedelta(days=days)).isoformat()
    with _get_conn() as conn:
        cur = conn.cursor()

        # Totals and averages
        cur.execute(
            """
            SELECT COUNT(*) AS total_emails,
                   AVG(COALESCE(confidence, 0)) AS avg_confidence,
                   AVG(COALESCE(processing_time, 0)) AS avg_processing_time
            FROM processed_emails
            WHERE timestamp >= ?
            """,
            (since,),
        )
        totals = _rows_to_dicts(cur, cur.fetchall())[0]

        # Last processed timestamp
        cur.execute(
            """
            SELECT timestamp FROM processed_emails
            ORDER BY timestamp DESC LIMIT 1
            """
        )
        row = cur.fetchone()
        last_processed = row[0] if row else None

        # Category breakdown (top categories)
        cur.execute(
            """
            SELECT category, COUNT(*) AS count
            FROM processed_emails
            WHERE timestamp >= ?
            GROUP BY category
            ORDER BY count DESC
            LIMIT 10
            """,
            (since,),
        )
        categories = _rows_to_dicts(cur, cur.fetchall())

        # Daily counts (for charting)
        cur.execute(
            """
            SELECT substr(timestamp, 1, 10) AS day, COUNT(*) AS count
            FROM processed_emails
            WHERE timestamp >= ?
            GROUP BY day
            ORDER BY day ASC
            """,
            (since,),
        )
        daily_counts = _rows_to_dicts(cur, cur.fetchall())

        # Recent emails
        cur.execute(
            """
            SELECT timestamp, subject, sender, category, confidence, sentiment
            FROM processed_emails
            ORDER BY timestamp DESC
            LIMIT 10
            """
        )
        recent_emails = _rows_to_dicts(cur, cur.fetchall())

    return {
        'total_emails': int(totals.get('total_emails', 0) or 0),
        'avg_confidence': float(totals.get('avg_confidence') or 0),
        'avg_processing_time': float(totals.get('avg_processing_time') or 0),
        'last_processed': last_processed,
        'categories': categories,
        'daily_counts': daily_counts,
        'recent_emails': recent_emails,
    }


def get_today_statistics() -> Dict[str, Any]:
    """Quick stats for today."""
    today_prefix = datetime.utcnow().strftime('%Y-%m-%d')
    with _get_conn() as conn:
        cur = conn.cursor()

        cur.execute(
            """
            SELECT COUNT(*) AS emails_today,
                   AVG(COALESCE(confidence, 0)) AS avg_confidence
            FROM processed_emails
            WHERE substr(timestamp, 1, 10) = ?
            """,
            (today_prefix,),
        )
        today = _rows_to_dicts(cur, cur.fetchall())[0]

        cur.execute(
            """
            SELECT category, COUNT(*) AS count
            FROM processed_emails
            WHERE substr(timestamp, 1, 10) = ?
            GROUP BY category
            ORDER BY count DESC
            """,
            (today_prefix,),
        )
        categories_today = _rows_to_dicts(cur, cur.fetchall())

    return {
        'emails_today': int(today.get('emails_today', 0) or 0),
        'avg_confidence': float(today.get('avg_confidence') or 0),
        'categories_today': categories_today,
    }