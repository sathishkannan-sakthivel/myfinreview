from sqlmodel import Session, select, create_engine, text
from config.settings import DATABASE_URL
import sys

def verify():
    print(f"Connecting to: {DATABASE_URL.split('@')[-1]}") # Print host only for security
    try:
        engine = create_engine(DATABASE_URL)
        with engine.connect() as connection:
            # Query to list all tables in public schema for Postgres
            result = connection.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema='public'"))
            tables = [row[0] for row in result]
            
            if not tables:
                print("No tables found in the database.")
            else:
                print("Found tables:")
                for table in tables:
                    print(f" - {table}")
                    
    except Exception as e:
        print(f"Error connecting to database: {e}")

if __name__ == "__main__":
    verify()
