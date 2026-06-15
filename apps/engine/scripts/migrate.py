"""Schema migration: add columns added after initial release."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from sqlalchemy import inspect, text
from db.base import engine


ADD_COLUMNS = {
    "chapters": [
        ("illustration_url", "VARCHAR"),
    ],
    "characters": [
        ("gender", "VARCHAR"),
        ("portrait_url", "VARCHAR"),
    ],
}


def run():
    inspector = inspect(engine)
    with engine.connect() as conn:
        for table, cols in ADD_COLUMNS.items():
            existing = {c["name"] for c in inspector.get_columns(table)}
            for col_name, col_type in cols:
                if col_name not in existing:
                    stmt = text(f"ALTER TABLE {table} ADD COLUMN {col_name} {col_type} NULL")
                    conn.execute(stmt)
                    print(f"  + added {table}.{col_name}")
                else:
                    print(f"  = {table}.{col_name} already exists")
        conn.commit()
    print("Migration complete.")


if __name__ == "__main__":
    run()
