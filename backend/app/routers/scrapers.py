"""Scrapers API router with job scraping management."""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel

from ..database import get_db
from ..models import ScrapingSession, JobPosting, User, UserProfile
from .users import get_current_user
from ..worker import scrape_jobs_task


router = APIRouter()


# Pydantic models
class ScrapeRequest(BaseModel):
    keywords: List[str]
    locations: List[str]
    sources: List[str] = ["linkedin"]
    max_results: int = 50
    min_salary: Optional[int] = None
    max_salary: Optional[int] = None
    job_types: Optional[List[str]] = None
    experience_levels: Optional[List[str]] = None
    date_posted: Optional[str] = None  # "24h", "3d", "1w", "1m"


class ScrapeResponse(BaseModel):
    task_id: str
    session_id: int
    message: str
    estimated_duration: str


class ScrapingSessionResponse(BaseModel):
    id: int
    source: str
    keywords: List[str]
    locations: List[str]
    status: str
    jobs_found: Optional[int]
    jobs_new: Optional[int]
    error_message: Optional[str]
    created_at: datetime
    completed_at: Optional[datetime]
    duration_seconds: Optional[int]

    class Config:
        from_attributes = True
        
    @property
    def duration(self) -> Optional[float]:
        """Calculate duration in minutes."""
        if self.completed_at and self.created_at:
            return (self.completed_at - self.created_at).total_seconds() / 60
        elif self.duration_seconds:
            return self.duration_seconds / 60
        return None


class ScrapingStats(BaseModel):
    total_sessions: int
    successful_sessions: int
    failed_sessions: int
    total_jobs_found: int
    total_new_jobs: int
    avg_jobs_per_session: float
    avg_duration_minutes: float
    sources_breakdown: Dict[str, int]
    last_scraping_date: Optional[datetime]


class JobPostingResponse(BaseModel):
    id: int
    title: str
    company: str
    location: str
    description: str
    requirements: Optional[str]
    salary_min: Optional[int]
    salary_max: Optional[int]
    job_type: Optional[str]
    source: str
    external_url: Optional[str]
    posted_date: Optional[datetime]
    scraped_at: datetime
    is_active: bool

    class Config:
        from_attributes = True


class SourceConfig(BaseModel):
    name: str
    enabled: bool
    max_results: int
    rate_limit_delay: float
    user_agent: Optional[str]
    proxy_enabled: bool
    stealth_mode: bool


# Routes
@router.post("/scrape", response_model=ScrapeResponse)
async def start_scraping(
    request: ScrapeRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Start a new job scraping session."""
    # Validate request
    if not request.keywords:
        raise HTTPException(status_code=400, detail="Keywords are required")
    
    if not request.locations:
        raise HTTPException(status_code=400, detail="Locations are required")
    
    # Check for recent scraping session to prevent abuse
    recent_session = db.query(ScrapingSession).filter(
        ScrapingSession.created_at >= datetime.utcnow() - timedelta(minutes=15)
    ).first()
    
    if recent_session and recent_session.status == "running":
        raise HTTPException(
            status_code=429,
            detail="A scraping session is already running. Please wait."
        )
    
    # Create scraping session
    session = ScrapingSession(
        source=",".join(request.sources),
        keywords=request.keywords,
        locations=request.locations,
        status="pending"
    )
    
    db.add(session)
    db.commit()
    db.refresh(session)
    
    # Start background task
    task = scrape_jobs_task.delay(
        keywords=request.keywords,
        locations=request.locations,
        sources=request.sources,
        max_results=request.max_results
    )
    
    # Update session with task ID
    session.task_id = task.id
    session.status = "running"
    db.commit()
    
    return ScrapeResponse(
        task_id=task.id,
        session_id=session.id,
        message="Scraping started successfully",
        estimated_duration="5-10 minutes"
    )


@router.get("/sessions", response_model=List[ScrapingSessionResponse])
async def get_scraping_sessions(
    skip: int = 0,
    limit: int = 20,
    status: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get scraping sessions with optional filtering."""
    query = db.query(ScrapingSession)
    
    if status:
        query = query.filter(ScrapingSession.status == status)
    
    sessions = query.order_by(ScrapingSession.created_at.desc()).offset(skip).limit(limit).all()
    
    return sessions


@router.get("/sessions/{session_id}", response_model=ScrapingSessionResponse)
async def get_scraping_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific scraping session."""
    session = db.query(ScrapingSession).filter(ScrapingSession.id == session_id).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Scraping session not found")
    
    return session


@router.delete("/sessions/{session_id}")
async def cancel_scraping_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Cancel a running scraping session."""
    session = db.query(ScrapingSession).filter(ScrapingSession.id == session_id).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Scraping session not found")
    
    if session.status not in ["pending", "running"]:
        raise HTTPException(
            status_code=400,
            detail="Can only cancel pending or running sessions"
        )
    
    # Cancel the Celery task if it exists
    if session.task_id:
        from ..worker import celery_app
        celery_app.control.revoke(session.task_id, terminate=True)
    
    # Update session status
    session.status = "cancelled"
    session.completed_at = datetime.utcnow()
    db.commit()
    
    return {"message": "Scraping session cancelled successfully"}


@router.get("/stats", response_model=ScrapingStats)
async def get_scraping_stats(
    days: int = 30,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get scraping statistics."""
    # Get sessions from the last N days
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    sessions = db.query(ScrapingSession).filter(
        ScrapingSession.created_at >= cutoff_date
    ).all()
    
    total_sessions = len(sessions)
    successful_sessions = len([s for s in sessions if s.status == "completed"])
    failed_sessions = len([s for s in sessions if s.status == "failed"])
    
    total_jobs_found = sum(s.jobs_found or 0 for s in sessions)
    total_new_jobs = sum(s.jobs_new or 0 for s in sessions)
    
    # Calculate averages
    avg_jobs_per_session = total_jobs_found / total_sessions if total_sessions > 0 else 0
    
    completed_sessions = [s for s in sessions if s.status == "completed" and s.completed_at]
    durations = [
        (s.completed_at - s.created_at).total_seconds() / 60
        for s in completed_sessions
    ]
    avg_duration_minutes = sum(durations) / len(durations) if durations else 0
    
    # Sources breakdown
    sources_breakdown = {}
    for session in sessions:
        if session.source:
            sources = session.source.split(',')
            for source in sources:
                source = source.strip()
                sources_breakdown[source] = sources_breakdown.get(source, 0) + 1
    
    # Last scraping date
    last_session = db.query(ScrapingSession).order_by(
        ScrapingSession.created_at.desc()
    ).first()
    
    last_scraping_date = last_session.created_at if last_session else None
    
    return ScrapingStats(
        total_sessions=total_sessions,
        successful_sessions=successful_sessions,
        failed_sessions=failed_sessions,
        total_jobs_found=total_jobs_found,
        total_new_jobs=total_new_jobs,
        avg_jobs_per_session=round(avg_jobs_per_session, 2),
        avg_duration_minutes=round(avg_duration_minutes, 2),
        sources_breakdown=sources_breakdown,
        last_scraping_date=last_scraping_date
    )


@router.get("/jobs", response_model=List[JobPostingResponse])
async def get_scraped_jobs(
    skip: int = 0,
    limit: int = 20,
    source: Optional[str] = None,
    company: Optional[str] = None,
    location: Optional[str] = None,
    days: int = 7,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get recently scraped job postings."""
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    query = db.query(JobPosting).filter(
        JobPosting.scraped_at >= cutoff_date,
        JobPosting.is_active == True
    )
    
    if source:
        query = query.filter(JobPosting.source == source)
    
    if company:
        query = query.filter(JobPosting.company.ilike(f"%{company}%"))
    
    if location:
        query = query.filter(JobPosting.location.ilike(f"%{location}%"))
    
    jobs = query.order_by(JobPosting.scraped_at.desc()).offset(skip).limit(limit).all()
    
    return jobs


@router.get("/sources", response_model=List[SourceConfig])
async def get_scraping_sources(
    current_user: User = Depends(get_current_user)
):
    """Get available scraping sources and their configurations."""
    sources = [
        SourceConfig(
            name="mock",
            enabled=True,
            max_results=15,
            rate_limit_delay=0.5,
            user_agent="MockScraper/1.0",
            proxy_enabled=False,
            stealth_mode=False
        ),
        SourceConfig(
            name="schema",
            enabled=True,
            max_results=50,
            rate_limit_delay=1.0,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            proxy_enabled=False,
            stealth_mode=False
        ),
        SourceConfig(
            name="linkedin",
            enabled=True,
            max_results=100,
            rate_limit_delay=2.0,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            proxy_enabled=False,
            stealth_mode=True
        ),
        SourceConfig(
            name="indeed",
            enabled=False,  # Not implemented yet
            max_results=50,
            rate_limit_delay=1.5,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            proxy_enabled=False,
            stealth_mode=True
        ),
        SourceConfig(
            name="glassdoor",
            enabled=False,  # Not implemented yet
            max_results=30,
            rate_limit_delay=3.0,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            proxy_enabled=False,
            stealth_mode=True
        )
    ]
    
    return sources


@router.post("/auto-scrape")
async def setup_auto_scraping(
    enabled: bool = True,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Enable or disable automatic daily scraping for the user."""
    profile = db.query(UserProfile).filter(
        UserProfile.user_id == current_user.id
    ).first()
    
    if not profile:
        raise HTTPException(status_code=404, detail="User profile not found")
    
    profile.auto_apply_enabled = enabled
    db.commit()
    
    return {
        "message": f"Auto-scraping {'enabled' if enabled else 'disabled'} successfully",
        "enabled": enabled
    }


@router.get("/keywords/suggestions")
async def get_keyword_suggestions(
    query: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get keyword suggestions based on existing job postings."""
    # Get unique keywords from job titles and descriptions
    job_titles = db.query(JobPosting.title).filter(
        JobPosting.title.ilike(f"%{query}%")
    ).distinct().limit(10).all()
    
    # Extract common keywords from job descriptions
    keywords = []
    for (title,) in job_titles:
        keywords.extend(title.split())
    
    # Remove duplicates and common words
    common_words = {"and", "or", "the", "a", "an", "in", "on", "at", "to", "for", "of", "with", "by"}
    unique_keywords = list(set(
        word.lower().strip(',.-()[]{}')
        for word in keywords
        if len(word) > 2 and word.lower() not in common_words
    ))
    
    return {"suggestions": unique_keywords[:20]}


@router.get("/locations/suggestions")
async def get_location_suggestions(
    query: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get location suggestions based on existing job postings."""
    locations = db.query(JobPosting.location).filter(
        JobPosting.location.ilike(f"%{query}%")
    ).distinct().limit(10).all()
    
    return {"suggestions": [loc[0] for loc in locations if loc[0]]}


@router.get("/health")
async def get_scraper_health():
    """Check the health of scraping services."""
    try:
        from ..worker import celery_app
        
        # Check Celery connection
        celery_status = celery_app.control.inspect().ping()
        celery_healthy = bool(celery_status)
        
        # Check if workers are active
        active_workers = celery_app.control.inspect().active()
        worker_count = len(active_workers) if active_workers else 0
        
        return {
            "status": "healthy" if celery_healthy else "unhealthy",
            "celery_connected": celery_healthy,
            "active_workers": worker_count,
            "services": {
                "mock_scraper": "available",
                "schema_scraper": "available",
                "linkedin_scraper": "available",
                "indeed_scraper": "coming_soon",
                "glassdoor_scraper": "coming_soon"
            }
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "celery_connected": False,
            "active_workers": 0
        } 