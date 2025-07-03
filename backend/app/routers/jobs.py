"""Jobs API router."""

from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel

from ..database import get_db
from ..models import JobPosting, JobMatch


router = APIRouter()


# Pydantic models for API
class JobPostingResponse(BaseModel):
    id: int
    title: str
    company: str
    location: str
    job_type: Optional[str]
    description: str
    source: str
    external_url: str
    is_active: bool

    class Config:
        from_attributes = True


class JobSearchRequest(BaseModel):
    keywords: List[str]
    locations: List[str] = []
    max_results: int = 50


@router.get("/", response_model=List[JobPostingResponse])
async def get_jobs(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    company: Optional[str] = None,
    location: Optional[str] = None,
    is_active: bool = True,
    db: Session = Depends(get_db)
):
    """Get all job postings with optional filtering."""
    query = db.query(JobPosting).filter(JobPosting.is_active == is_active)
    
    if company:
        query = query.filter(JobPosting.company.ilike(f"%{company}%"))
    if location:
        query = query.filter(JobPosting.location.ilike(f"%{location}%"))
    
    jobs = query.offset(skip).limit(limit).all()
    return jobs


@router.get("/{job_id}", response_model=JobPostingResponse)
async def get_job(job_id: int, db: Session = Depends(get_db)):
    """Get a specific job posting by ID."""
    job = db.query(JobPosting).filter(JobPosting.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.get("/stats/summary")
async def get_job_stats(db: Session = Depends(get_db)):
    """Get job statistics summary."""
    total_jobs = db.query(JobPosting).count()
    active_jobs = db.query(JobPosting).filter(JobPosting.is_active == True).count()
    
    return {
        "total_jobs": total_jobs,
        "active_jobs": active_jobs,
        "message": "Job stats retrieved successfully"
    } 