"""Applications API router with full application management."""

from typing import List, Optional
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel

from ..database import get_db
from ..models import (
    JobApplication, JobPosting, CoverLetter, JobMatch, 
    ApplicationStatus, User, UserProfile
)
from .users import get_current_user
from ..worker import generate_cover_letter_task


router = APIRouter()


# Pydantic models
class ApplicationCreate(BaseModel):
    job_posting_id: int
    cover_letter_id: Optional[int] = None
    application_method: str = "email"  # email, portal, linkedin
    email_sent_to: Optional[str] = None
    portal_url: Optional[str] = None
    notes: Optional[str] = None


class ApplicationUpdate(BaseModel):
    status: Optional[ApplicationStatus] = None
    response_received: Optional[bool] = None
    response_date: Optional[datetime] = None
    response_type: Optional[str] = None  # rejection, interview, offer, etc.
    response_notes: Optional[str] = None
    interview_scheduled: Optional[datetime] = None
    interview_completed: Optional[bool] = None
    interview_notes: Optional[str] = None
    follow_up_scheduled: Optional[datetime] = None
    follow_up_completed: Optional[bool] = None


class ApplicationResponse(BaseModel):
    id: int
    user_id: int
    job_posting_id: int
    cover_letter_id: Optional[int]
    status: ApplicationStatus
    application_method: str
    submitted_at: Optional[datetime]
    email_sent_to: Optional[str]
    portal_url: Optional[str]
    response_received: bool
    response_date: Optional[datetime]
    response_type: Optional[str]
    response_notes: Optional[str]
    interview_scheduled: Optional[datetime]
    interview_completed: bool
    interview_notes: Optional[str]
    follow_up_scheduled: Optional[datetime]
    follow_up_completed: bool
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class ApplicationWithDetails(BaseModel):
    id: int
    status: ApplicationStatus
    application_method: str
    submitted_at: Optional[datetime]
    response_received: bool
    response_date: Optional[datetime]
    response_type: Optional[str]
    job_posting: dict  # Job posting details
    cover_letter: Optional[dict] = None  # Cover letter details
    created_at: datetime

    class Config:
        from_attributes = True


class ApplicationStats(BaseModel):
    total_applications: int
    pending: int
    submitted: int
    under_review: int
    interviews_scheduled: int
    offers_received: int
    rejected: int
    response_rate: float
    interview_rate: float
    offer_rate: float


class CoverLetterGenerationRequest(BaseModel):
    job_posting_id: int
    tone: str = "professional"
    length: str = "medium"
    focus_areas: Optional[List[str]] = None
    custom_instructions: Optional[str] = None


# Routes
@router.post("/", response_model=ApplicationResponse)
async def create_application(
    application_data: ApplicationCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new job application."""
    # Verify job posting exists
    job_posting = db.query(JobPosting).filter(
        JobPosting.id == application_data.job_posting_id
    ).first()
    
    if not job_posting:
        raise HTTPException(status_code=404, detail="Job posting not found")
    
    # Check if application already exists
    existing_application = db.query(JobApplication).filter(
        JobApplication.user_id == current_user.id,
        JobApplication.job_posting_id == application_data.job_posting_id
    ).first()
    
    if existing_application:
        raise HTTPException(
            status_code=400, 
            detail="Application already exists for this job"
        )
    
    # Create application
    application = JobApplication(
        user_id=current_user.id,
        job_posting_id=application_data.job_posting_id,
        cover_letter_id=application_data.cover_letter_id,
        status=ApplicationStatus.PENDING,
        application_method=application_data.application_method,
        email_sent_to=application_data.email_sent_to,
        portal_url=application_data.portal_url
    )
    
    db.add(application)
    db.commit()
    db.refresh(application)
    
    # If no cover letter provided, generate one in background
    if not application_data.cover_letter_id:
        background_tasks.add_task(
            generate_cover_letter_for_application,
            application.id
        )
    
    return application


@router.get("/", response_model=List[ApplicationWithDetails])
async def get_applications(
    skip: int = 0,
    limit: int = 20,
    status: Optional[ApplicationStatus] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's job applications with details."""
    query = db.query(JobApplication).filter(JobApplication.user_id == current_user.id)
    
    if status:
        query = query.filter(JobApplication.status == status)
    
    applications = query.offset(skip).limit(limit).all()
    
    # Enrich with job posting and cover letter details
    enriched_applications = []
    for app in applications:
        app_dict = {
            "id": app.id,
            "status": app.status,
            "application_method": app.application_method,
            "submitted_at": app.submitted_at,
            "response_received": app.response_received,
            "response_date": app.response_date,
            "response_type": app.response_type,
            "created_at": app.created_at,
            "job_posting": {
                "id": app.job_posting.id,
                "title": app.job_posting.title,
                "company": app.job_posting.company,
                "location": app.job_posting.location,
                "external_url": app.job_posting.external_url
            }
        }
        
        if app.cover_letter:
            app_dict["cover_letter"] = {
                "id": app.cover_letter.id,
                "tone": app.cover_letter.tone,
                "length": app.cover_letter.length,
                "is_approved": app.cover_letter.is_approved
            }
        
        enriched_applications.append(app_dict)
    
    return enriched_applications


@router.get("/{application_id}", response_model=ApplicationResponse)
async def get_application(
    application_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific application."""
    application = db.query(JobApplication).filter(
        JobApplication.id == application_id,
        JobApplication.user_id == current_user.id
    ).first()
    
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    
    return application


@router.put("/{application_id}", response_model=ApplicationResponse)
async def update_application(
    application_id: int,
    update_data: ApplicationUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update application status and details."""
    application = db.query(JobApplication).filter(
        JobApplication.id == application_id,
        JobApplication.user_id == current_user.id
    ).first()
    
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    
    # Update fields
    for field, value in update_data.dict(exclude_unset=True).items():
        setattr(application, field, value)
    
    # Auto-set submitted_at when status changes to submitted
    if update_data.status == ApplicationStatus.SUBMITTED and not application.submitted_at:
        application.submitted_at = datetime.utcnow()
    
    db.commit()
    db.refresh(application)
    return application


@router.delete("/{application_id}")
async def delete_application(
    application_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete an application."""
    application = db.query(JobApplication).filter(
        JobApplication.id == application_id,
        JobApplication.user_id == current_user.id
    ).first()
    
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    
    db.delete(application)
    db.commit()
    return {"message": "Application deleted successfully"}


@router.post("/{application_id}/submit")
async def submit_application(
    application_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Submit an application (send email or apply via portal)."""
    application = db.query(JobApplication).filter(
        JobApplication.id == application_id,
        JobApplication.user_id == current_user.id
    ).first()
    
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    
    if application.status != ApplicationStatus.PENDING:
        raise HTTPException(
            status_code=400,
            detail="Application can only be submitted from pending status"
        )
    
    # TODO: Implement actual email sending or portal submission
    # For now, just update the status
    application.status = ApplicationStatus.SUBMITTED
    application.submitted_at = datetime.utcnow()
    
    db.commit()
    db.refresh(application)
    
    return {"message": "Application submitted successfully"}


@router.post("/generate-cover-letter")
async def generate_cover_letter(
    request: CoverLetterGenerationRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate a cover letter for a job posting."""
    # Verify job posting exists
    job_posting = db.query(JobPosting).filter(
        JobPosting.id == request.job_posting_id
    ).first()
    
    if not job_posting:
        raise HTTPException(status_code=404, detail="Job posting not found")
    
    # Check if cover letter already exists
    existing_letter = db.query(CoverLetter).filter(
        CoverLetter.user_id == current_user.id,
        CoverLetter.job_posting_id == request.job_posting_id
    ).first()
    
    if existing_letter:
        return {
            "message": "Cover letter already exists",
            "cover_letter_id": existing_letter.id
        }
    
    # Create job match if doesn't exist (for cover letter generation)
    job_match = db.query(JobMatch).filter(
        JobMatch.user_id == current_user.id,
        JobMatch.job_posting_id == request.job_posting_id
    ).first()
    
    if not job_match:
        # Create a basic job match
        job_match = JobMatch(
            user_id=current_user.id,
            job_posting_id=request.job_posting_id,
            overall_score=0.8,  # Default score
            skills_score=0.8,
            experience_score=0.8,
            location_score=1.0,
            salary_score=0.8,
            matching_keywords=[],
            missing_requirements=[]
        )
        db.add(job_match)
        db.commit()
        db.refresh(job_match)
    
    # Generate cover letter in background
    user_preferences = {
        "tone": request.tone,
        "length": request.length,
        "focus_areas": request.focus_areas,
        "custom_instructions": request.custom_instructions
    }
    
    task = generate_cover_letter_task.delay(job_match.id, user_preferences)
    
    return {
        "message": "Cover letter generation started",
        "task_id": task.id,
        "job_match_id": job_match.id
    }


@router.get("/stats/summary", response_model=ApplicationStats)
async def get_application_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get application statistics for the user."""
    applications = db.query(JobApplication).filter(
        JobApplication.user_id == current_user.id
    ).all()
    
    total_applications = len(applications)
    
    if total_applications == 0:
        return ApplicationStats(
            total_applications=0,
            pending=0,
            submitted=0,
            under_review=0,
            interviews_scheduled=0,
            offers_received=0,
            rejected=0,
            response_rate=0.0,
            interview_rate=0.0,
            offer_rate=0.0
        )
    
    # Count by status
    status_counts = {}
    for app in applications:
        status = app.status.value if hasattr(app.status, 'value') else str(app.status)
        status_counts[status] = status_counts.get(status, 0) + 1
    
    # Calculate rates
    submitted_count = status_counts.get("submitted", 0) + status_counts.get("under_review", 0)
    responses = len([app for app in applications if app.response_received])
    interviews = len([app for app in applications if app.interview_scheduled])
    offers = status_counts.get("offer_received", 0)
    
    response_rate = (responses / submitted_count) if submitted_count > 0 else 0.0
    interview_rate = (interviews / submitted_count) if submitted_count > 0 else 0.0
    offer_rate = (offers / submitted_count) if submitted_count > 0 else 0.0
    
    return ApplicationStats(
        total_applications=total_applications,
        pending=status_counts.get("pending", 0),
        submitted=status_counts.get("submitted", 0),
        under_review=status_counts.get("under_review", 0),
        interviews_scheduled=interviews,
        offers_received=offers,
        rejected=status_counts.get("rejected", 0),
        response_rate=round(response_rate, 3),
        interview_rate=round(interview_rate, 3),
        offer_rate=round(offer_rate, 3)
    )


# Helper functions
async def generate_cover_letter_for_application(application_id: int):
    """Background task to generate cover letter for an application."""
    # This would be called as a background task
    # Implementation would use the generate_cover_letter_task
    pass 