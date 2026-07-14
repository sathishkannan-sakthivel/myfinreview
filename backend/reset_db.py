from sqlmodel import SQLModel, create_engine
from config.settings import DATABASE_URL

def reset_database():
    print("WARNING: This will drop all tables in your Aiven database.")
    engine = create_engine(DATABASE_URL)
    
    # Import all models to ensure SQLModel knows about them
    from models.portable_models import User, Holding, Transaction, Insight, NewsArticle, AlertRule, AlertEvent, AnalyticsSummary, PriceCache, NewsHash
    
    print("Dropping all tables...")
    SQLModel.metadata.drop_all(engine)
    
    print("Recreating all tables with new schema...")
    SQLModel.metadata.create_all(engine)
    
    print("Database reset successfully!")

if __name__ == "__main__":
    reset_database()
