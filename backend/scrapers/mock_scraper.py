"""
Mock scraper for testing and demonstration purposes.
This scraper generates realistic fake job data to test the application.
"""

import random
from datetime import datetime, timedelta
from typing import List, Optional
from .base_scraper import BaseScraper, JobData
import logging


class MockScraper(BaseScraper):
    """Mock scraper that generates fake job data for testing."""
    
    def __init__(self):
        super().__init__()
        
        # Sample data for generating realistic jobs
        self.companies = [
            "TechCorp Inc", "DataCo", "AI Solutions LLC", "DevStudio", "CloudWorks",
            "InnovateLab", "StartupXYZ", "BigTech Co", "WebDev Agency", "FinTech Pro",
            "GreenTech Solutions", "HealthTech Inc", "EduTech Platform", "GameDev Studio",
            "CyberSec Corp", "MobileDev Inc", "BlockChain Co", "IoT Innovations"
        ]
        
        self.job_titles = [
            "Software Engineer", "Senior Python Developer", "Full Stack Developer",
            "Backend Developer", "Frontend Developer", "DevOps Engineer",
            "Data Scientist", "Machine Learning Engineer", "Product Manager",
            "Software Architect", "Technical Lead", "QA Engineer",
            "Security Engineer", "Mobile Developer", "Cloud Engineer",
            "Site Reliability Engineer", "Platform Engineer", "Solutions Architect"
        ]
        
        self.locations = [
            "Remote", "San Francisco, CA", "New York, NY", "Seattle, WA",
            "Austin, TX", "Boston, MA", "Chicago, IL", "Los Angeles, CA",
            "Denver, CO", "Atlanta, GA", "Portland, OR", "Miami, FL",
            "Washington, DC", "Toronto, ON", "Vancouver, BC", "London, UK"
        ]
        
        self.job_types = ["full_time", "part_time", "contract", "internship", "remote"]
        
        self.tech_skills = [
            "Python", "JavaScript", "TypeScript", "React", "Node.js", "Django",
            "FastAPI", "PostgreSQL", "MongoDB", "Redis", "Docker", "Kubernetes",
            "AWS", "Azure", "GCP", "Git", "CI/CD", "REST APIs", "GraphQL",
            "Microservices", "TensorFlow", "PyTorch", "Pandas", "NumPy",
            "Linux", "Agile", "Scrum", "Jest", "Pytest", "Selenium"
        ]

    async def setup_browser(self):
        """Mock scraper doesn't need a browser."""
        print("Mock scraper setup - no browser needed")
        return True

    async def cleanup(self):
        """Mock scraper doesn't need cleanup."""
        print("Mock scraper cleanup - no browser to close")
        return True
    
    async def login(self):
        """Mock login - always succeeds."""
        print("Mock scraper login - always successful")
        return True
    
    async def search_jobs(
        self,
        keywords: List[str],
        locations: List[str],
        job_types: Optional[List[str]] = None,
        salary_min: Optional[int] = None,
        max_results: int = 50
    ) -> List[JobData]:
        """Generate mock job data based on search criteria."""
        print(f"Mock scraper searching for jobs with keywords: {keywords}, locations: {locations}")
        
        jobs = []
        num_jobs = min(max_results, random.randint(5, 15))  # Generate 5-15 jobs
        
        for i in range(num_jobs):
            # Select random data
            company = random.choice(self.companies)
            title = random.choice(self.job_titles)
            location = random.choice(locations) if locations else random.choice(self.locations)
            job_type = random.choice(self.job_types)
            
            # Generate realistic salary ranges
            base_salary = random.randint(70, 200) * 1000
            salary_min_val = base_salary
            salary_max_val = base_salary + random.randint(20, 50) * 1000
            
            # Generate description with keywords
            selected_skills = random.sample(self.tech_skills, random.randint(3, 8))
            
            description = f"""
We are seeking a talented {title} to join our {company} team. 

Key Responsibilities:
- Develop and maintain high-quality software applications
- Collaborate with cross-functional teams to deliver innovative solutions
- Write clean, efficient, and well-documented code
- Participate in code reviews and architectural discussions
- Stay up-to-date with latest technologies and best practices

Required Skills:
{', '.join(selected_skills[:5])}

Preferred Skills:
{', '.join(selected_skills[5:] if len(selected_skills) > 5 else selected_skills)}

We offer competitive compensation, comprehensive benefits, and opportunities for professional growth.
            """.strip()
            
            requirements = f"Required: {', '.join(selected_skills[:3])}\nPreferred: {', '.join(selected_skills[3:6])}"
            
            benefits = "Health insurance, 401(k) matching, flexible PTO, remote work options, professional development budget"
            
            # Generate posting date (within last 30 days)
            posted_date = datetime.utcnow() - timedelta(days=random.randint(1, 30))
            
            job = JobData(
                title=title,
                company=company,
                location=location,
                description=description,
                requirements=requirements,
                benefits=benefits,
                salary_min=salary_min_val,
                salary_max=salary_max_val,
                job_type=job_type,
                application_url=f"https://{company.lower().replace(' ', '')}.com/careers/apply/{i+1}",
                application_email=f"careers@{company.lower().replace(' ', '')}.com",
                external_id=f"mock_{company.replace(' ', '_').lower()}_{i+1}",
                external_url=f"https://{company.lower().replace(' ', '')}.com/careers/{i+1}",
                posted_date=posted_date,
                source="mock"
            )
            
            jobs.append(job)
            
        print(f"Mock scraper generated {len(jobs)} jobs")
        return jobs
    
    async def get_job_details(self, job_url: str) -> Optional[JobData]:
        """Mock implementation - not needed for this scraper."""
        return None 