from __future__ import annotations

import os
import random
import sys

from dotenv import load_dotenv
import psycopg2
from psycopg2 import Error


def get_database_url() -> str:
    load_dotenv()
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL is not set. Copy .env.example to .env and update it.")
    return database_url


def main() -> int:
    connection = None
    cursor = None

    try:
        database_url = get_database_url()
        connection = psycopg2.connect(database_url)
        cursor = connection.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS telemetry_logs (
                id SERIAL PRIMARY KEY,
                temperature NUMERIC(5, 2) NOT NULL,
                humidity NUMERIC(5, 2) NOT NULL
            )
            """
        )

        cursor.execute(
            """
            SELECT id, temperature, humidity
            FROM telemetry_logs
            ORDER BY id DESC
            LIMIT 5
            """
        )
        existing_columns = [column[0] for column in cursor.description]
        existing_rows = cursor.fetchall()
        print(f"Existing rows before insert ({existing_columns}): {existing_rows}")

        temperature = round(random.uniform(18.0, 24.0), 2)
        humidity = round(random.uniform(30.0, 55.0), 2)

        cursor.execute(
            """
            INSERT INTO telemetry_logs (temperature, humidity)
            VALUES (%s, %s)
            RETURNING id, temperature, humidity
            """,
            (temperature, humidity),
        )
        inserted_row = cursor.fetchone()
        inserted_columns = [column[0] for column in cursor.description]
        connection.commit()

        cursor.execute(
            """
            SELECT id, temperature, humidity
            FROM telemetry_logs
            WHERE id = %s
            """,
            (inserted_row[0],),
        )
        fetched_row = cursor.fetchone()
        fetched_columns = [column[0] for column in cursor.description]
        print(f"Inserted test row ({inserted_columns}): {inserted_row}")
        print(f"Database connection successful. Retrieved row ({fetched_columns}): {fetched_row}")
        return 0
    except (ValueError, Error) as exc:
        if connection is not None:
            connection.rollback()
        print(f"Database test failed: {exc}", file=sys.stderr)
        return 1
    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None:
            connection.close()


if __name__ == "__main__":
    raise SystemExit(main())
