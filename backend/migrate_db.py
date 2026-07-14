from sqlmodel import create_engine, text
from config.settings import DATABASE_URL

def migrate():
    print("Connecting to database for migration...")
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as connection:
        # 1. Add target_allocation and drift_sensitivity to User table
        try:
            print("Adding 'target_allocation' to 'user' table...")
            connection.execute(text('ALTER TABLE "user" ADD COLUMN IF NOT EXISTS target_allocation VARCHAR'))
            connection.commit()
            print("Adding 'drift_sensitivity' to 'user' table...")
            connection.execute(text('ALTER TABLE "user" ADD COLUMN IF NOT EXISTS drift_sensitivity FLOAT DEFAULT 5.0'))
            connection.commit()
            print("Success.")
        except Exception as e:
            print(f"Note: Could not update user table columns: {e}")

        # 2. Add hash to Transaction table
        try:
            print("Adding 'hash' to 'transaction' table...")
            connection.execute(text('ALTER TABLE "transaction" ADD COLUMN IF NOT EXISTS hash VARCHAR'))
            connection.commit()
            connection.execute(text('CREATE UNIQUE INDEX IF NOT EXISTS ix_transaction_hash ON "transaction" (hash)'))
            connection.commit()
            print("Success.")
        except Exception as e:
            print(f"Note: Could not add hash to transaction (may already exist): {e}")

        # 3. Add data_json to AnalyticsSummary if missing
        try:
            print("Adding 'data_json' to 'analyticssummary' table...")
            connection.execute(text('ALTER TABLE "analyticssummary" ADD COLUMN IF NOT EXISTS data_json VARCHAR'))
            connection.commit()
            print("Success.")
        except Exception as e:
            print(f"Note: Could not add data_json to analyticssummary: {e}")

        # 4. Rename old average_price column if it exists (legacy schema)
        try:
            print("Checking for legacy 'average_price' column on 'holding'...")
            connection.execute(text('ALTER TABLE holding RENAME COLUMN average_price TO avg_price'))
            connection.commit()
            print("Renamed average_price -> avg_price.")
        except Exception as e:
            # this may fail if column does not exist or already renamed; ignore
            print(f"Note: average_price rename skipped or not needed: {e}")

    print("Migration complete.")

if __name__ == "__main__":
    migrate()
