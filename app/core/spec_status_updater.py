"""
Utility to update spec statuses based on completion percentage.
"""

import sqlite3
from app.core.config import Config


def update_all_spec_statuses(db_path: str = None):
    """Update status for all specs based on completion."""
    db_path = db_path or Config.SQLITE_DB_PATH
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Update all spec statuses
    cursor.execute("""
        UPDATE specs SET
            status = CASE
                WHEN total_tasks = 0 THEN 'planning'
                WHEN completed_tasks = 0 THEN 'planning'
                WHEN completed_tasks = total_tasks THEN 'completed'
                ELSE 'in_progress'
            END,
            updated_at = CURRENT_TIMESTAMP
    """)

    rows_updated = cursor.rowcount
    conn.commit()
    conn.close()

    return {"updated": rows_updated}


if __name__ == "__main__":
    result = update_all_spec_statuses()
    print(f"Updated {result['updated']} specs")
