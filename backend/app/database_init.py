"""Database initialization script."""

import asyncio
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from loguru import logger

from .config import settings
from .database import Base, engine
from .models import (
    User, UserProfile, JobPosting, JobMatch, CoverLetter,
    JobApplication, Contact, ScrapingSession, SystemLog
)


def create_database_if_not_exists():
    """Create database if it doesn't exist."""
    try:
        # Extract database name from URL
        db_url_parts = settings.database_url.split('/')
        db_name = db_url_parts[-1]
        
        # Create connection to PostgreSQL without specifying database
        base_url = '/'.join(db_url_parts[:-1])
        base_engine = create_engine(base_url + '/postgres')
        
        # Check if database exists
        with base_engine.connect() as conn:
            result = conn.execute(
                text("SELECT 1 FROM pg_catalog.pg_database WHERE datname = :db_name"),
                {"db_name": db_name}
            )
            
            if not result.fetchone():
                # Create database
                conn.execute(text("COMMIT"))
                conn.execute(text(f"CREATE DATABASE {db_name}"))
                logger.info(f"Created database: {db_name}")
            else:
                logger.info(f"Database {db_name} already exists")
        
        base_engine.dispose()
        
    except SQLAlchemyError as e:
        logger.error(f"Failed to create database: {e}")
        raise


def create_tables():
    """Create all database tables."""
    try:
        # Create all tables
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
        
    except SQLAlchemyError as e:
        logger.error(f"Failed to create tables: {e}")
        raise


def create_indexes():
    """Create additional indexes for performance."""
    try:
        with engine.connect() as conn:
            # Job postings indexes
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_job_postings_title 
                ON job_postings USING gin(to_tsvector('english', title))
            """))
            
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_job_postings_company 
                ON job_postings (company)
            """))
            
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_job_postings_location 
                ON job_postings (location)
            """))
            
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_job_postings_source 
                ON job_postings (source)
            """))
            
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_job_postings_scraped_at 
                ON job_postings (scraped_at)
            """))
            
            # Job matches indexes
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_job_matches_score 
                ON job_matches (overall_score)
            """))
            
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_job_matches_user_score 
                ON job_matches (user_id, overall_score)
            """))
            
            # Applications indexes
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_job_applications_status 
                ON job_applications (status)
            """))
            
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_job_applications_user_status 
                ON job_applications (user_id, status)
            """))
            
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_job_applications_submitted_at 
                ON job_applications (submitted_at)
            """))
            
            # Cover letters indexes
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_cover_letters_user_approved 
                ON cover_letters (user_id, is_approved)
            """))
            
            # Scraping sessions indexes
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_scraping_sessions_status 
                ON scraping_sessions (status)
            """))
            
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_scraping_sessions_created_at 
                ON scraping_sessions (created_at)
            """))
            
            conn.commit()
            logger.info("Database indexes created successfully")
            
    except SQLAlchemyError as e:
        logger.error(f"Failed to create indexes: {e}")
        raise


def create_extensions():
    """Create PostgreSQL extensions."""
    try:
        with engine.connect() as conn:
            # Create text search extension
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS pg_trgm"))
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS btree_gin"))
            conn.commit()
            logger.info("PostgreSQL extensions created successfully")
            
    except SQLAlchemyError as e:
        logger.error(f"Failed to create extensions: {e}")
        # Don't raise here as extensions might not be available in all environments
        logger.warning("Continuing without extensions")


def seed_initial_data():
    """Seed database with initial data."""
    try:
        from .database import SessionLocal
        
        db = SessionLocal()
        
        # Check if we already have data
        if db.query(User).count() > 0:
            logger.info("Database already has data, skipping seeding")
            db.close()
            return
        
        # Create a sample user (for testing)
        sample_user = User(
            email="demo@autoapply.ai",
            full_name="Demo User",
            hashed_password="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewpZxJMN8KjEqkL6",  # "password"
            is_active=True
        )
        
        db.add(sample_user)
        db.commit()
        db.refresh(sample_user)
        
        # Create sample user profile
        sample_profile = UserProfile(
            user_id=sample_user.id,
            phone="+1-555-0123",
            address="123 Main St, San Francisco, CA 94105",
            linkedin_url="https://linkedin.com/in/demouser",
            skills=["Python", "JavaScript", "Machine Learning", "Web Development"],
            preferred_locations=["San Francisco", "Remote"],
            preferred_job_types=["Full-time", "Contract"],
            keywords=["software engineer", "python developer", "backend developer"],
            salary_min=80000,
            salary_max=150000,
            auto_apply_enabled=False,
            daily_application_limit=5,
            min_match_score=0.7
        )
        
        db.add(sample_profile)
        db.commit()
        
        logger.info("Initial data seeded successfully")
        db.close()
        
    except SQLAlchemyError as e:
        logger.error(f"Failed to seed initial data: {e}")
        raise


def init_database():
    """Initialize the complete database."""
    logger.info("Starting database initialization...")
    
    try:
        # Step 1: Create database if it doesn't exist
        create_database_if_not_exists()
        
        # Step 2: Create extensions
        create_extensions()
        
        # Step 3: Create tables
        create_tables()
        
        # Step 4: Create indexes
        create_indexes()
        
        # Step 5: Seed initial data
        seed_initial_data()
        
        logger.info("Database initialization completed successfully!")
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise


def reset_database():
    """Reset database by dropping and recreating all tables."""
    logger.warning("Resetting database - all data will be lost!")
    
    try:
        # Drop all tables
        Base.metadata.drop_all(bind=engine)
        logger.info("All tables dropped")
        
        # Recreate tables
        create_tables()
        
        # Create indexes
        create_indexes()
        
        # Seed initial data
        seed_initial_data()
        
        logger.info("Database reset completed successfully!")
        
    except Exception as e:
        logger.error(f"Database reset failed: {e}")
        raise


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "reset":
        reset_database()
    else:
        init_database() 