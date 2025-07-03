"""Dashboard API router with analytics and metrics."""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from pydantic import BaseModel

from ..database import get_db
from ..models import (
    JobApplication, JobPosting, CoverLetter, JobMatch, 
    ApplicationStatus, User, UserProfile, ScrapingSession
)
from .users import get_current_user


router = APIRouter()


# Pydantic models
class DashboardOverview(BaseModel):
    total_applications: int
    pending_applications: int
    submitted_applications: int
    interviews_scheduled: int
    offers_received: int
    response_rate: float
    interview_rate: float
    offer_rate: float
    recent_activity: List[dict]
    job_matches_count: int
    cover_letters_count: int
    active_job_postings: int


class ApplicationTrend(BaseModel):
    date: str
    applications: int
    interviews: int
    offers: int
    rejections: int


class JobMatchingSummary(BaseModel):
    total_matches: int
    high_matches: int  # > 0.8 score
    medium_matches: int  # 0.6-0.8 score
    low_matches: int  # < 0.6 score
    approved_matches: int
    pending_matches: int
    top_matching_companies: List[Dict[str, Any]]
    top_matching_skills: List[Dict[str, Any]]


class CoverLetterStats(BaseModel):
    total_generated: int
    approved: int
    pending_approval: int
    rejected: int
    avg_generation_time: float
    most_used_tone: str
    most_used_length: str


class ScrapingActivity(BaseModel):
    total_sessions: int
    jobs_scraped: int
    new_jobs_found: int
    last_scraping_date: Optional[datetime]
    sources_breakdown: Dict[str, int]


class ActivityItem(BaseModel):
    id: int
    type: str  # application, match, cover_letter, scraping
    title: str
    description: str
    timestamp: datetime
    status: Optional[str] = None
    link: Optional[str] = None


# Routes
@router.get("/overview", response_model=DashboardOverview)
async def get_dashboard_overview(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get dashboard overview with key metrics."""
    # Get all applications
    applications = db.query(JobApplication).filter(
        JobApplication.user_id == current_user.id
    ).all()
    
    # Calculate basic metrics
    total_applications = len(applications)
    pending_applications = len([app for app in applications if app.status == ApplicationStatus.PENDING])
    submitted_applications = len([app for app in applications if app.status == ApplicationStatus.SUBMITTED])
    interviews_scheduled = len([app for app in applications if app.interview_scheduled])
    offers_received = len([app for app in applications if app.status == ApplicationStatus.OFFER_RECEIVED])
    
    # Calculate rates
    response_rate = 0.0
    interview_rate = 0.0
    offer_rate = 0.0
    
    if submitted_applications > 0:
        responses = len([app for app in applications if app.response_received])
        response_rate = responses / submitted_applications
        interview_rate = interviews_scheduled / submitted_applications
        offer_rate = offers_received / submitted_applications
    
    # Get job matches count
    job_matches_count = db.query(JobMatch).filter(
        JobMatch.user_id == current_user.id
    ).count()
    
    # Get cover letters count
    cover_letters_count = db.query(CoverLetter).filter(
        CoverLetter.user_id == current_user.id
    ).count()
    
    # Get active job postings count
    active_job_postings = db.query(JobPosting).filter(
        JobPosting.is_active == True
    ).count()
    
    # Get recent activity
    recent_activity = await get_recent_activity(current_user.id, db, limit=10)
    
    return DashboardOverview(
        total_applications=total_applications,
        pending_applications=pending_applications,
        submitted_applications=submitted_applications,
        interviews_scheduled=interviews_scheduled,
        offers_received=offers_received,
        response_rate=round(response_rate, 3),
        interview_rate=round(interview_rate, 3),
        offer_rate=round(offer_rate, 3),
        recent_activity=recent_activity,
        job_matches_count=job_matches_count,
        cover_letters_count=cover_letters_count,
        active_job_postings=active_job_postings
    )


@router.get("/trends", response_model=List[ApplicationTrend])
async def get_application_trends(
    days: int = Query(30, ge=7, le=365),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get application trends over time."""
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    # Get applications in date range
    applications = db.query(JobApplication).filter(
        JobApplication.user_id == current_user.id,
        JobApplication.created_at >= start_date
    ).all()
    
    # Group by date
    trends = defaultdict(lambda: {
        'applications': 0,
        'interviews': 0,
        'offers': 0,
        'rejections': 0
    })
    
    for app in applications:
        date_str = app.created_at.strftime('%Y-%m-%d')
        trends[date_str]['applications'] += 1
        
        if app.interview_scheduled:
            trends[date_str]['interviews'] += 1
        if app.status == ApplicationStatus.OFFER_RECEIVED:
            trends[date_str]['offers'] += 1
        if app.status == ApplicationStatus.REJECTED:
            trends[date_str]['rejections'] += 1
    
    # Fill in missing dates with zeros
    result = []
    current_date = start_date
    while current_date <= end_date:
        date_str = current_date.strftime('%Y-%m-%d')
        trend_data = trends[date_str]
        
        result.append(ApplicationTrend(
            date=date_str,
            applications=trend_data['applications'],
            interviews=trend_data['interviews'],
            offers=trend_data['offers'],
            rejections=trend_data['rejections']
        ))
        
        current_date += timedelta(days=1)
    
    return result


@router.get("/job-matching", response_model=JobMatchingSummary)
async def get_job_matching_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get job matching summary and statistics."""
    # Get all job matches
    job_matches = db.query(JobMatch).filter(
        JobMatch.user_id == current_user.id
    ).all()
    
    total_matches = len(job_matches)
    high_matches = len([m for m in job_matches if m.overall_score > 0.8])
    medium_matches = len([m for m in job_matches if 0.6 <= m.overall_score <= 0.8])
    low_matches = len([m for m in job_matches if m.overall_score < 0.6])
    approved_matches = len([m for m in job_matches if m.is_approved])
    pending_matches = len([m for m in job_matches if not m.is_approved])
    
    # Get top matching companies
    company_scores = defaultdict(list)
    for match in job_matches:
        company_scores[match.job_posting.company].append(match.overall_score)
    
    top_companies = []
    for company, scores in company_scores.items():
        avg_score = sum(scores) / len(scores)
        top_companies.append({
            'company': company,
            'avg_score': round(avg_score, 3),
            'match_count': len(scores)
        })
    
    top_companies.sort(key=lambda x: x['avg_score'], reverse=True)
    top_matching_companies = top_companies[:10]
    
    # Get top matching skills
    skill_counts = defaultdict(int)
    for match in job_matches:
        for skill in match.matching_keywords or []:
            skill_counts[skill] += 1
    
    top_matching_skills = [
        {'skill': skill, 'count': count}
        for skill, count in sorted(skill_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    ]
    
    return JobMatchingSummary(
        total_matches=total_matches,
        high_matches=high_matches,
        medium_matches=medium_matches,
        low_matches=low_matches,
        approved_matches=approved_matches,
        pending_matches=pending_matches,
        top_matching_companies=top_matching_companies,
        top_matching_skills=top_matching_skills
    )


@router.get("/cover-letters", response_model=CoverLetterStats)
async def get_cover_letter_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get cover letter statistics."""
    cover_letters = db.query(CoverLetter).filter(
        CoverLetter.user_id == current_user.id
    ).all()
    
    total_generated = len(cover_letters)
    approved = len([cl for cl in cover_letters if cl.is_approved])
    pending_approval = len([cl for cl in cover_letters if not cl.is_approved and not cl.is_rejected])
    rejected = len([cl for cl in cover_letters if cl.is_rejected])
    
    # Calculate average generation time
    generation_times = [cl.generation_time for cl in cover_letters if cl.generation_time]
    avg_generation_time = sum(generation_times) / len(generation_times) if generation_times else 0.0
    
    # Get most used tone and length
    tone_counts = defaultdict(int)
    length_counts = defaultdict(int)
    
    for cl in cover_letters:
        if cl.tone:
            tone_counts[cl.tone] += 1
        if cl.length:
            length_counts[cl.length] += 1
    
    most_used_tone = max(tone_counts.items(), key=lambda x: x[1])[0] if tone_counts else "professional"
    most_used_length = max(length_counts.items(), key=lambda x: x[1])[0] if length_counts else "medium"
    
    return CoverLetterStats(
        total_generated=total_generated,
        approved=approved,
        pending_approval=pending_approval,
        rejected=rejected,
        avg_generation_time=round(avg_generation_time, 2),
        most_used_tone=most_used_tone,
        most_used_length=most_used_length
    )


@router.get("/scraping-activity", response_model=ScrapingActivity)
async def get_scraping_activity(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get scraping activity summary."""
    # Get all scraping sessions
    sessions = db.query(ScrapingSession).all()
    
    total_sessions = len(sessions)
    jobs_scraped = sum(session.jobs_found or 0 for session in sessions)
    new_jobs_found = sum(session.jobs_new or 0 for session in sessions)
    
    # Get last scraping date
    last_session = db.query(ScrapingSession).order_by(
        ScrapingSession.created_at.desc()
    ).first()
    
    last_scraping_date = last_session.created_at if last_session else None
    
    # Get sources breakdown
    sources_breakdown = defaultdict(int)
    for session in sessions:
        if session.source:
            sources = session.source.split(',')
            for source in sources:
                sources_breakdown[source.strip()] += 1
    
    return ScrapingActivity(
        total_sessions=total_sessions,
        jobs_scraped=jobs_scraped,
        new_jobs_found=new_jobs_found,
        last_scraping_date=last_scraping_date,
        sources_breakdown=dict(sources_breakdown)
    )


@router.get("/activity", response_model=List[ActivityItem])
async def get_activity_feed(
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user activity feed."""
    return await get_recent_activity(current_user.id, db, limit)


# Helper functions
async def get_recent_activity(user_id: int, db: Session, limit: int = 10) -> List[dict]:
    """Get recent activity for a user."""
    activities = []
    
    # Get recent applications
    recent_applications = db.query(JobApplication).filter(
        JobApplication.user_id == user_id
    ).order_by(JobApplication.created_at.desc()).limit(limit).all()
    
    for app in recent_applications:
        activities.append({
            'id': app.id,
            'type': 'application',
            'title': f"Applied to {app.job_posting.title}",
            'description': f"at {app.job_posting.company}",
            'timestamp': app.created_at,
            'status': app.status.value if hasattr(app.status, 'value') else str(app.status),
            'link': f"/applications/{app.id}"
        })
    
    # Get recent job matches
    recent_matches = db.query(JobMatch).filter(
        JobMatch.user_id == user_id
    ).order_by(JobMatch.created_at.desc()).limit(limit).all()
    
    for match in recent_matches:
        activities.append({
            'id': match.id,
            'type': 'match',
            'title': f"New job match: {match.job_posting.title}",
            'description': f"at {match.job_posting.company} ({match.overall_score:.1%} match)",
            'timestamp': match.created_at,
            'status': 'approved' if match.is_approved else 'pending',
            'link': f"/jobs/{match.job_posting_id}"
        })
    
    # Get recent cover letters
    recent_cover_letters = db.query(CoverLetter).filter(
        CoverLetter.user_id == user_id
    ).order_by(CoverLetter.created_at.desc()).limit(limit).all()
    
    for cl in recent_cover_letters:
        activities.append({
            'id': cl.id,
            'type': 'cover_letter',
            'title': f"Cover letter generated",
            'description': f"for {cl.job_posting.title} at {cl.job_posting.company}",
            'timestamp': cl.created_at,
            'status': 'approved' if cl.is_approved else 'pending',
            'link': f"/cover-letters/{cl.id}"
        })
    
    # Sort all activities by timestamp
    activities.sort(key=lambda x: x['timestamp'], reverse=True)
    
    return activities[:limit] 