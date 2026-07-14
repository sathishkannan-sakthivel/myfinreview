import os

import psycopg2


DATABASE_URL = os.getenv("DATABASE_URL")


def migrate():
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL is required for PostgreSQL migrations.")

    print("Attempting lite migration via psycopg2...")
    try:
        conn = psycopg2.connect(DATABASE_URL)
        conn.autocommit = True
        cur = conn.cursor()

        print("Checking/Adding 'drift_sensitivity' to 'user' table...")
        try:
            cur.execute('ALTER TABLE "user" ADD COLUMN drift_sensitivity FLOAT DEFAULT 5.0')
            print("Success: Column added.")
        except Exception as e:
            if "already exists" in str(e):
                print("Note: Column already exists.")
            else:
                print(f"Error adding column: {e}")

        cur.close()
        conn.close()
        print("Lite migration complete.")
    except Exception as e:
        print(f"FATAL Migration Error: {e}")


if __name__ == "__main__":
    migrate()