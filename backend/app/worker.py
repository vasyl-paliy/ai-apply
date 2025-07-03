"""Celery worker for background tasks."""

import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass

from celery import Celery
from sqlalchemy.orm import Session
from loguru import logger

from .config import settings
from .database import SessionLocal, get_db
from .models import (
    JobPosting, UserProfile, JobMatch, CoverLetter, 
    JobApplication, ScrapingSession, SystemLog
)
from ..scrapers.linkedin_scraper import LinkedInScraper
from ..scrapers.mock_scraper import MockScraper
from ..scrapers.schema_scraper import SchemaScraper
from ..scrapers.base_scraper import JobData
from ..generators.cover_letter_generator import (
    CoverLetterGenerator, CoverLetterRequest
)


# Initialize Celery
celery_app = Celery(
    "autoapply_ai",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=['backend.app.worker']
)

# Celery configuration
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

# Scheduled tasks
celery_app.conf.beat_schedule = {
    'daily-job-scraping': {
        'task': 'backend.app.worker.daily_job_scraping',
        'schedule': 60.0 * 60.0 * 24.0,  # Daily at midnight
        'args': ()
    },
    'generate-pending-cover-letters': {
        'task': 'backend.app.worker.generate_pending_cover_letters',
        'schedule': 60.0 * 30.0,  # Every 30 minutes
        'args': ()
    },
    'send-approved-applications': {
        'task': 'backend.app.worker.send_approved_applications',
        'schedule': 60.0 * 60.0,  # Every hour
        'args': ()
    },
}


@dataclass
class MatchScore:
    overall_score: float
    skills_score: float
    experience_score: float
    location_score: float
    salary_score: float
    matching_keywords: List[str]
    missing_requirements: List[str]


def get_db_session():
    """Get database session for tasks."""
    return SessionLocal()


@celery_app.task(bind=True)
def scrape_jobs_task(self, keywords: List[str], locations: List[str], 
                    sources: Optional[List[str]] = None, max_results: int = 50):
    """Background task to scrape jobs from various sources."""
    if sources is None:
        sources = ["linkedin"]
    
    db = get_db_session()
    session_id = None
    
    try:
        # Find existing session by task ID
        session = db.query(ScrapingSession).filter(
            ScrapingSession.task_id == self.request.id,
            ScrapingSession.status == "running"
        ).first()
        
        if not session:
            # Fallback: create new session if not found
            session = ScrapingSession(
                source=",".join(sources or []),
                keywords=keywords,
                locations=locations,
                status="running",
                task_id=self.request.id
            )
            db.add(session)
            db.commit()
        
        session_id = session.id
        
        all_jobs = []
        
        # Use asyncio to run the async scrapers
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # LinkedIn scraping
            if "linkedin" in sources:
                try:
                    async def scrape_linkedin():
                        async with LinkedInScraper() as scraper:
                            return await scraper.scrape_jobs(
                                keywords=keywords,
                                locations=locations,
                                max_results=max_results
                            )
                    
                    linkedin_jobs = loop.run_until_complete(scrape_linkedin())
                    
                    # Save jobs to database
                    new_jobs = 0
                    for job_data in linkedin_jobs:
                        existing_job = db.query(JobPosting).filter(
                            JobPosting.external_id == job_data.external_id,
                            JobPosting.source == job_data.source
                        ).first()
                        
                        if not existing_job:
                            job_posting = JobPosting(
                                title=job_data.title,
                                company=job_data.company,
                                location=job_data.location,
                                description=job_data.description,
                                requirements=job_data.requirements,
                                benefits=job_data.benefits,
                                salary_min=job_data.salary_min,
                                salary_max=job_data.salary_max,
                                job_type=job_data.job_type,
                                source=job_data.source,
                                external_id=job_data.external_id,
                                external_url=job_data.external_url,
                                application_url=job_data.application_url,
                                application_email=job_data.application_email,
                                posted_date=job_data.posted_date
                            )
                            db.add(job_posting)
                            new_jobs += 1
                            all_jobs.append(job_posting)
                    
                    # Commit jobs to get IDs
                    if new_jobs > 0:
                        db.commit()
                        db.refresh(session)  # Refresh session to get updated data
                    
                    logger.info(f"LinkedIn scraping: {len(linkedin_jobs)} found, {new_jobs} new")
                    
                except Exception as e:
                    logger.error(f"LinkedIn scraping failed: {e}")
                    # Continue with other sources

            # Mock scraping
            if "mock" in sources:
                try:
                    logger.info("Starting mock scraping...")
                    # Mock scraper doesn't need async event loop
                    scraper = MockScraper()
                    logger.info("MockScraper created, calling search_jobs directly...")
                    mock_jobs = loop.run_until_complete(scraper.search_jobs(
                        keywords=keywords,
                        locations=locations,
                        max_results=max_results
                    ))
                    logger.info(f"Mock scraping completed, got {len(mock_jobs)} jobs")
                    
                    # Save jobs to database
                    new_jobs = 0
                    for job_data in mock_jobs:
                        existing_job = db.query(JobPosting).filter(
                            JobPosting.external_id == job_data.external_id,
                            JobPosting.source == job_data.source
                        ).first()
                        
                        if not existing_job:
                            job_posting = JobPosting(
                                title=job_data.title,
                                company=job_data.company,
                                location=job_data.location,
                                description=job_data.description,
                                requirements=job_data.requirements,
                                benefits=job_data.benefits,
                                salary_min=job_data.salary_min,
                                salary_max=job_data.salary_max,
                                job_type=job_data.job_type,
                                source=job_data.source,
                                external_id=job_data.external_id,
                                external_url=job_data.external_url,
                                application_url=job_data.application_url,
                                application_email=job_data.application_email,
                                posted_date=job_data.posted_date
                            )
                            db.add(job_posting)
                            new_jobs += 1
                            all_jobs.append(job_posting)
                    
                    # Commit jobs to get IDs
                    if new_jobs > 0:
                        db.commit()
                        db.refresh(session)  # Refresh session to get updated data
                    
                    logger.info(f"Mock scraping: {len(mock_jobs)} found, {new_jobs} new")
                    
                except Exception as e:
                    logger.error(f"Mock scraping failed: {e}")
                    # Continue with other sources

            # Schema scraping
            if "schema" in sources:
                try:
                    async def scrape_schema():
                        async with SchemaScraper() as scraper:
                            return await scraper.scrape_jobs(
                                keywords=keywords,
                                locations=locations,
                                max_results=max_results
                            )
                    
                    schema_jobs = loop.run_until_complete(scrape_schema())
                    
                    # Save jobs to database
                    new_jobs = 0
                    for job_data in schema_jobs:
                        existing_job = db.query(JobPosting).filter(
                            JobPosting.external_id == job_data.external_id,
                            JobPosting.source == job_data.source
                        ).first()
                        
                        if not existing_job:
                            job_posting = JobPosting(
                                title=job_data.title,
                                company=job_data.company,
                                location=job_data.location,
                                description=job_data.description,
                                requirements=job_data.requirements,
                                benefits=job_data.benefits,
                                salary_min=job_data.salary_min,
                                salary_max=job_data.salary_max,
                                job_type=job_data.job_type,
                                source=job_data.source,
                                external_id=job_data.external_id,
                                external_url=job_data.external_url,
                                application_url=job_data.application_url,
                                application_email=job_data.application_email,
                                posted_date=job_data.posted_date
                            )
                            db.add(job_posting)
                            new_jobs += 1
                            all_jobs.append(job_posting)
                    
                    # Commit jobs to get IDs
                    if new_jobs > 0:
                        db.commit()
                        db.refresh(session)  # Refresh session to get updated data
                    
                    logger.info(f"Schema scraping: {len(schema_jobs)} found, {new_jobs} new")
                    
                except Exception as e:
                    logger.error(f"Schema scraping failed: {e}")
                    # Continue with other sources
                    
        finally:
            loop.close()
        
        # Update session
        session.jobs_found = len(all_jobs)
        session.jobs_new = len([j for j in all_jobs if j.id is None])
        session.status = "completed"
        session.completed_at = datetime.utcnow()
        
        db.commit()
        
        # Trigger job matching for all users
        match_jobs_for_all_users.delay([job.id for job in all_jobs if job.id])
        
        return {
            "jobs_found": len(all_jobs),
            "jobs_new": session.jobs_new,
            "session_id": session_id
        }
        
    except Exception as e:
        logger.error(f"Job scraping task failed: {e}")
        
        # Update session with error
        if session_id:
            session = db.query(ScrapingSession).get(session_id)
            if session:
                session.status = "failed"
                session.error_message = str(e)
                session.completed_at = datetime.utcnow()
                db.commit()
        
        raise
    finally:
        db.close()


@celery_app.task(bind=True)
def match_jobs_for_user(self, user_id: int, job_ids: List[int] = None):
    """Calculate job matches for a specific user."""
    db = get_db_session()
    
    try:
        user_profile = db.query(UserProfile).filter(
            UserProfile.user_id == user_id
        ).first()
        
        if not user_profile:
            logger.warning(f"No profile found for user {user_id}")
            return {"matches_created": 0}
        
        # Get jobs to match
        if job_ids:
            jobs = db.query(JobPosting).filter(JobPosting.id.in_(job_ids)).all()
        else:
            # Match against recent jobs
            cutoff_date = datetime.utcnow() - timedelta(days=7)
            jobs = db.query(JobPosting).filter(
                JobPosting.scraped_at >= cutoff_date,
                JobPosting.is_active == True
            ).limit(100).all()
        
        matches_created = 0
        
        for job in jobs:
            # Check if match already exists
            existing_match = db.query(JobMatch).filter(
                JobMatch.user_id == user_id,
                JobMatch.job_posting_id == job.id
            ).first()
            
            if existing_match:
                continue
            
            # Calculate match score
            match_score = calculate_job_match_score(job, user_profile)
            
            if match_score.overall_score >= user_profile.min_match_score:
                job_match = JobMatch(
                    user_id=user_id,
                    job_posting_id=job.id,
                    overall_score=match_score.overall_score,
                    skills_score=match_score.skills_score,
                    experience_score=match_score.experience_score,
                    location_score=match_score.location_score,
                    salary_score=match_score.salary_score,
                    matching_keywords=match_score.matching_keywords,
                    missing_requirements=match_score.missing_requirements
                )
                db.add(job_match)
                matches_created += 1
        
        db.commit()
        
        logger.info(f"Created {matches_created} job matches for user {user_id}")
        return {"matches_created": matches_created}
        
    except Exception as e:
        logger.error(f"Job matching failed for user {user_id}: {e}")
        raise
    finally:
        db.close()


@celery_app.task(bind=True)
def match_jobs_for_all_users(self, job_ids: List[int]):
    """Calculate job matches for all active users."""
    db = get_db_session()
    
    try:
        # Get all users with profiles
        user_profiles = db.query(UserProfile).all()
        
        total_matches = 0
        for profile in user_profiles:
            result = match_jobs_for_user.delay(profile.user_id, job_ids)
            # Note: In production, you might want to track these results
        
        logger.info(f"Triggered job matching for {len(user_profiles)} users")
        return {"users_processed": len(user_profiles)}
        
    except Exception as e:
        logger.error(f"Batch job matching failed: {e}")
        raise
    finally:
        db.close()


@celery_app.task(bind=True)
def generate_cover_letter_task(self, job_match_id: int, user_preferences: Optional[Dict[str, Any]] = None):
    """Generate a cover letter for a job match."""
    db = get_db_session()
    
    try:
        # Get job match and related data
        job_match = db.query(JobMatch).filter(JobMatch.id == job_match_id).first()
        if not job_match:
            raise ValueError(f"Job match {job_match_id} not found")
        
        user_profile = db.query(UserProfile).filter(
            UserProfile.user_id == job_match.user_id
        ).first()
        
        if not user_profile:
            raise ValueError(f"User profile for user {job_match.user_id} not found")
        
        # Check if cover letter already exists
        existing_letter = db.query(CoverLetter).filter(
            CoverLetter.user_id == job_match.user_id,
            CoverLetter.job_posting_id == job_match.job_posting_id
        ).first()
        
        if existing_letter:
            logger.info(f"Cover letter already exists for job match {job_match_id}")
            return {"cover_letter_id": existing_letter.id, "generated": False}
        
        # Prepare job data
        job_data = JobData(
            title=job_match.job_posting.title,
            company=job_match.job_posting.company,
            location=job_match.job_posting.location,
            description=job_match.job_posting.description,
            requirements=job_match.job_posting.requirements,
            benefits=job_match.job_posting.benefits,
            salary_min=job_match.job_posting.salary_min,
            salary_max=job_match.job_posting.salary_max,
            job_type=job_match.job_posting.job_type,
            application_url=job_match.job_posting.application_url,
            application_email=job_match.job_posting.application_email,
            external_id=job_match.job_posting.external_id,
            external_url=job_match.job_posting.external_url,
            posted_date=job_match.job_posting.posted_date,
            source=job_match.job_posting.source
        )
        
        # Prepare user profile data
        profile_data = {
            'full_name': user_profile.user.full_name,
            'skills': user_profile.skills or [],
            'experience': user_profile.experience or [],
            'education': user_profile.education or []
        }
        
        # Set preferences
        tone = user_preferences.get('tone', 'professional') if user_preferences else 'professional'
        length = user_preferences.get('length', 'medium') if user_preferences else 'medium'
        
        # Generate cover letter
        generator = CoverLetterGenerator()
        request = CoverLetterRequest(
            job_data=job_data,
            user_profile=profile_data,
            tone=tone,
            length=length
        )
        
        # Run async function in sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        response = loop.run_until_complete(generator.generate(request))
        loop.close()
        
        # Save cover letter
        cover_letter = CoverLetter(
            user_id=job_match.user_id,
            job_posting_id=job_match.job_posting_id,
            content=response.content,
            tone=response.tone,
            length=response.length,
            model_used=response.model_used,
            tokens_used=response.tokens_used,
            generation_time=response.generation_time
        )
        db.add(cover_letter)
        db.commit()
        
        logger.info(f"Generated cover letter {cover_letter.id} for job match {job_match_id}")
        return {
            "cover_letter_id": cover_letter.id, 
            "generated": True,
            "quality_score": response.quality_score
        }
        
    except Exception as e:
        logger.error(f"Cover letter generation failed for job match {job_match_id}: {e}")
        raise
    finally:
        db.close()


@celery_app.task(bind=True)
def daily_job_scraping(self):
    """Daily task to scrape jobs for all users."""
    db = get_db_session()
    
    try:
        # Get unique keywords and locations from all user profiles
        profiles = db.query(UserProfile).filter(UserProfile.auto_apply_enabled == True).all()
        
        if not profiles:
            logger.info("No users with auto-apply enabled")
            return {"message": "No users to scrape for"}
        
        all_keywords = set()
        all_locations = set()
        
        for profile in profiles:
            if profile.keywords:
                all_keywords.update(profile.keywords)
            if profile.preferred_locations:
                all_locations.update(profile.preferred_locations)
        
        # Trigger scraping task
        scrape_jobs_task.delay(
            keywords=list(all_keywords),
            locations=list(all_locations),
            sources=["mock", "schema", "linkedin"],
            max_results=100
        )
        
        logger.info(f"Triggered daily scraping for {len(profiles)} users")
        return {"users": len(profiles), "keywords": len(all_keywords)}
        
    except Exception as e:
        logger.error(f"Daily job scraping failed: {e}")
        raise
    finally:
        db.close()


@celery_app.task(bind=True)
def generate_pending_cover_letters(self):
    """Generate cover letters for approved job matches."""
    db = get_db_session()
    
    try:
        # Find approved matches without cover letters
        matches_needing_letters = db.query(JobMatch).filter(
            JobMatch.is_approved == True,
            ~JobMatch.job_posting_id.in_(
                db.query(CoverLetter.job_posting_id).filter(
                    CoverLetter.user_id == JobMatch.user_id
                )
            )
        ).limit(10).all()  # Limit to avoid overwhelming the system
        
        for match in matches_needing_letters:
            generate_cover_letter_task.delay(match.id)
        
        logger.info(f"Triggered cover letter generation for {len(matches_needing_letters)} matches")
        return {"cover_letters_triggered": len(matches_needing_letters)}
        
    except Exception as e:
        logger.error(f"Pending cover letter generation failed: {e}")
        raise
    finally:
        db.close()


@celery_app.task(bind=True)
def send_approved_applications(self):
    """Send approved applications via email."""
    # This would be implemented when email functionality is added
    logger.info("Send approved applications task - email functionality to be implemented")
    return {"applications_sent": 0}


def calculate_job_match_score(job: JobPosting, profile: UserProfile) -> MatchScore:
    """Calculate how well a job matches a user profile."""
    skills_score = 0.0
    experience_score = 0.5
    location_score = 0.0
    salary_score = 0.0
    matching_keywords = []
    missing_requirements = []
    
    # Skills matching
    if profile.skills and job.description:
        job_text = (job.description + " " + (job.requirements or "")).lower()
        user_skills = [skill.lower() for skill in profile.skills]
        
        matched_skills = [skill for skill in user_skills if skill in job_text]
        matching_keywords.extend(matched_skills)
        
        if user_skills:
            skills_score = len(matched_skills) / len(user_skills)
    
    # Location matching
    if profile.preferred_locations and job.location:
        job_location = job.location.lower()
        preferred_locations = [loc.lower() for loc in profile.preferred_locations]
        
        for location in preferred_locations:
            if location in job_location or job_location in location:
                location_score = 1.0
                break
            elif "remote" in location and "remote" in job_location:
                location_score = 1.0
                break
        else:
            location_score = 0.3
    
    # Salary matching
    if profile.salary_min and job.salary_min:
        if job.salary_min >= profile.salary_min:
            salary_score = 1.0
        else:
            # Partial score based on how close it is
            salary_score = max(0, job.salary_min / profile.salary_min)
    elif job.salary_min or job.salary_max:
        salary_score = 0.5  # Some salary info is better than none
    
    # Keyword matching
    if profile.keywords and job.description:
        job_text = (job.title + " " + job.description + " " + (job.requirements or "")).lower()
        user_keywords = [kw.lower() for kw in profile.keywords]
        
        matched_keywords = [kw for kw in user_keywords if kw in job_text]
        matching_keywords.extend(matched_keywords)
        
        keyword_score = len(matched_keywords) / len(user_keywords) if user_keywords else 0
    else:
        keyword_score = 0
    
    # Calculate overall score (weighted average)
    overall_score = (
        skills_score * 0.4 +
        keyword_score * 0.3 +
        location_score * 0.2 +
        salary_score * 0.1 +
        experience_score * 0.1
    )
    
    return MatchScore(
        overall_score=overall_score,
        skills_score=skills_score,
        experience_score=experience_score,
        location_score=location_score,
        salary_score=salary_score,
        matching_keywords=list(set(matching_keywords)),
        missing_requirements=missing_requirements
    ) 