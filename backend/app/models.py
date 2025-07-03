"""SQLAlchemy models for AutoApply AI."""

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean, Column, DateTime, Float, ForeignKey, Integer, 
    String, Text, JSON, Enum as SQLEnum
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from .database import Base


class ApplicationStatus(enum.Enum):
    """Status of job applications."""
    PENDING = "pending"
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    INTERVIEW_SCHEDULED = "interview_scheduled"
    INTERVIEW_COMPLETED = "interview_completed"
    OFFER_RECEIVED = "offer_received"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"


class JobType(enum.Enum):
    """Types of job positions."""
    FULL_TIME = "full_time"
    PART_TIME = "part_time"
    CONTRACT = "contract"
    INTERNSHIP = "internship"
    REMOTE = "remote"
    HYBRID = "hybrid"


class User(Base):
    """User account."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    profiles = relationship("UserProfile", back_populates="user")
    job_applications = relationship("JobApplication", back_populates="user")
    cover_letters = relationship("CoverLetter", back_populates="user")


class UserProfile(Base):
    """User profile with resume data and preferences."""
    __tablename__ = "user_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    
    # Personal Information
    phone = Column(String)
    address = Column(Text)
    linkedin_url = Column(String)
    portfolio_url = Column(String)
    
    # Resume Data
    resume_text = Column(Text)
    skills = Column(JSON)  # List of skills
    experience = Column(JSON)  # Work experience data
    education = Column(JSON)  # Education data
    
    # Job Preferences
    preferred_locations = Column(JSON)  # List of preferred cities
    preferred_job_types = Column(JSON)  # List of job types
    preferred_industries = Column(JSON)  # List of industries
    keywords = Column(JSON)  # List of job keywords
    salary_min = Column(Integer)
    salary_max = Column(Integer)
    
    # Settings
    auto_apply_enabled = Column(Boolean, default=False)
    daily_application_limit = Column(Integer, default=5)
    min_match_score = Column(Float, default=0.7)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="profiles")


class JobPosting(Base):
    """Job posting from various sources."""
    __tablename__ = "job_postings"

    id = Column(Integer, primary_key=True, index=True)
    
    # Basic Information
    title = Column(String, nullable=False, index=True)
    company = Column(String, nullable=False, index=True)
    location = Column(String, index=True)
    job_type = Column(SQLEnum(JobType, values_callable=lambda x: [e.value for e in x]))
    
    # Job Details
    description = Column(Text)
    requirements = Column(Text)
    benefits = Column(Text)
    salary_min = Column(Integer)
    salary_max = Column(Integer)
    
    # Source Information
    source = Column(String, nullable=False)  # linkedin, indeed, etc.
    external_id = Column(String, unique=True, index=True)
    external_url = Column(String)
    application_url = Column(String)
    application_email = Column(String)
    
    # Processing Status
    is_processed = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    
    # Metadata
    posted_date = Column(DateTime(timezone=True))
    scraped_at = Column(DateTime(timezone=True), server_default=func.now())
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    job_applications = relationship("JobApplication", back_populates="job_posting")
    job_matches = relationship("JobMatch", back_populates="job_posting")


class JobMatch(Base):
    """Matching score between user profile and job posting."""
    __tablename__ = "job_matches"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    job_posting_id = Column(Integer, ForeignKey("job_postings.id"))
    
    # Matching Scores
    overall_score = Column(Float, nullable=False)
    skills_score = Column(Float)
    experience_score = Column(Float)
    location_score = Column(Float)
    salary_score = Column(Float)
    
    # Matching Details
    matching_keywords = Column(JSON)  # Keywords that matched
    missing_requirements = Column(JSON)  # Requirements not met
    
    # Status
    is_reviewed = Column(Boolean, default=False)
    is_approved = Column(Boolean, default=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    job_posting = relationship("JobPosting", back_populates="job_matches")


class CoverLetter(Base):
    """Generated cover letters."""
    __tablename__ = "cover_letters"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    job_posting_id = Column(Integer, ForeignKey("job_postings.id"))
    
    # Content
    content = Column(Text, nullable=False)
    tone = Column(String)  # formal, casual, enthusiastic, etc.
    length = Column(String)  # short, medium, long
    
    # Generation Details
    model_used = Column(String)
    tokens_used = Column(Integer)
    generation_time = Column(Float)
    
    # Status
    is_approved = Column(Boolean, default=False)
    is_sent = Column(Boolean, default=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="cover_letters")
    job_applications = relationship("JobApplication", back_populates="cover_letter")


class JobApplication(Base):
    """Job application tracking."""
    __tablename__ = "job_applications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    job_posting_id = Column(Integer, ForeignKey("job_postings.id"))
    cover_letter_id = Column(Integer, ForeignKey("cover_letters.id"))
    
    # Application Details
    status = Column(SQLEnum(ApplicationStatus), default=ApplicationStatus.PENDING)
    application_method = Column(String)  # email, portal, linkedin
    
    # Submission Details
    submitted_at = Column(DateTime(timezone=True))
    email_sent_to = Column(String)
    portal_url = Column(String)
    
    # Follow-up Information
    follow_up_scheduled = Column(DateTime(timezone=True))
    follow_up_completed = Column(Boolean, default=False)
    
    # Response Tracking
    response_received = Column(Boolean, default=False)
    response_date = Column(DateTime(timezone=True))
    response_type = Column(String)  # rejection, interview, etc.
    response_notes = Column(Text)
    
    # Interview Information
    interview_scheduled = Column(DateTime(timezone=True))
    interview_completed = Column(Boolean, default=False)
    interview_notes = Column(Text)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="job_applications")
    job_posting = relationship("JobPosting", back_populates="job_applications")
    cover_letter = relationship("CoverLetter", back_populates="job_applications")
    contacts = relationship("Contact", back_populates="job_application")


class Contact(Base):
    """Contacts for follow-up and networking."""
    __tablename__ = "contacts"

    id = Column(Integer, primary_key=True, index=True)
    job_application_id = Column(Integer, ForeignKey("job_applications.id"))
    
    # Contact Information
    name = Column(String)
    title = Column(String)
    company = Column(String)
    email = Column(String)
    linkedin_url = Column(String)
    phone = Column(String)
    
    # Contact Source
    source = Column(String)  # linkedin, company_website, hunter_io, etc.
    confidence_score = Column(Float)  # How confident we are this is the right person
    
    # Outreach Status
    contacted = Column(Boolean, default=False)
    contact_date = Column(DateTime(timezone=True))
    contact_method = Column(String)  # email, linkedin, phone
    response_received = Column(Boolean, default=False)
    response_date = Column(DateTime(timezone=True))
    
    # Notes
    notes = Column(Text)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    job_application = relationship("JobApplication", back_populates="contacts")


class ScrapingSession(Base):
    """Track scraping sessions and results."""
    __tablename__ = "scraping_sessions"

    id = Column(Integer, primary_key=True, index=True)
    
    # Session Details
    source = Column(String, nullable=False)
    keywords = Column(JSON)
    locations = Column(JSON)
    job_types = Column(JSON)
    
    # Task Management
    task_id = Column(String)  # Celery task ID
    
    # Results
    jobs_found = Column(Integer, default=0)
    jobs_new = Column(Integer, default=0)
    jobs_updated = Column(Integer, default=0)
    
    # Status
    status = Column(String, default="running")  # running, completed, failed
    error_message = Column(Text)
    
    # Timing
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))
    duration_seconds = Column(Integer)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class SystemLog(Base):
    """System logs for monitoring and debugging."""
    __tablename__ = "system_logs"

    id = Column(Integer, primary_key=True, index=True)
    
    # Log Details
    level = Column(String, nullable=False)  # INFO, WARNING, ERROR, DEBUG
    module = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    
    # Context
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    job_posting_id = Column(Integer, ForeignKey("job_postings.id"), nullable=True)
    application_id = Column(Integer, ForeignKey("job_applications.id"), nullable=True)
    
    # Additional Data
    extra_data = Column(JSON)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now()) 