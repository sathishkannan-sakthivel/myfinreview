from sqlmodel import create_engine, Session, SQLModel
import os
from dotenv import load_dotenv
from config.settings import DATABASE_URL
import logging

logger = logging.getLogger(__name__)

load_dotenv()

# Determine if we are using SQLite for local development
is_sqlite = DATABASE_URL.startswith("sqlite")

if is_sqlite:
    # SQLite-specific configuration
    engine = create_engine(
        DATABASE_URL, 
        echo=False, 
        connect_args={"check_same_thread": False}
    )
else:
    # Advanced pooling and keepalives for PostgreSQL (Aiven/Supabase)
    engine = create_engine(
        DATABASE_URL, 
        echo=False, 
        pool_pre_ping=True, 
        pool_recycle=60, 
        pool_size=15,    
        max_overflow=5,  
        connect_args={
            "connect_timeout": 30,
            "keepalives": 1,
            "keepalives_idle": 30,
            "keepalives_interval": 10,
            "keepalives_count": 5
        }
    )

def get_session():
    with Session(engine) as session:
        yield session

def init_db():
    from sqlalchemy import inspect
    # Import all models to ensure metadata is populated
    from models.portable_models import User, Holding, Transaction, Insight, NewsArticle, AlertRule, AlertEvent, AnalyticsSummary, PriceCache, NewsHash
    
    inspector = inspect(engine)
    if not inspector.has_table("user"):
        logger.info("Tables not found. Creating database schema.")
        SQLModel.metadata.create_all(engine)
    else:
        logger.info("Database already initialized. Skipping create_all.")
