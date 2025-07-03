"""
Indeed scraper using gentle techniques and rate limiting.
Indeed is less strict than LinkedIn but still requires careful handling.
"""

import asyncio
import re
from datetime import datetime, timedelta
from typing import List, Optional
from urllib.parse import urlencode, urlparse
from .base_scraper import BaseScraper, JobData
import random


class IndeedScraper(BaseScraper):
    """Indeed job scraper with respectful rate limiting."""
    
    def __init__(self):
        super().__init__()
        self.base_url = "https://www.indeed.com"
        self.session_cookies = {}
        
    async def login(self):
        """Indeed doesn't require login for basic searching."""
        try:
            if not self.page:
                await self.setup_browser()
                
            if not self.page:
                print("Failed to setup browser")
                return False
                
            # Visit homepage to get session cookies
            await self.page.goto(self.base_url, wait_until="domcontentloaded")
            await self.wait_between_requests()
            
            # Get session cookies
            cookies = await self.page.context.cookies()
            self.session_cookies = {cookie['name']: cookie['value'] for cookie in cookies}
            
            print("Indeed session established successfully")
            return True
            
        except Exception as e:
            print(f"Indeed session setup failed: {e}")
            return False
    
    async def search_jobs(
        self,
        keywords: List[str],
        locations: List[str],
        job_types: Optional[List[str]] = None,
        salary_min: Optional[int] = None,
        max_results: int = 50
    ) -> List[JobData]:
        """Search for jobs on Indeed."""
        
        jobs = []
        
        try:
            for location in locations:
                for keyword in keywords:
                    print(f"Searching Indeed for '{keyword}' in '{location}'")
                    
                    # Build search URL
                    search_params = {
                        'q': keyword,
                        'l': location,
                        'fromage': '14',  # Last 14 days
                        'sort': 'date',
                        'limit': min(50, max_results)  # Indeed shows max 50 per page
                    }
                    
                    if salary_min:
                        search_params['salary'] = f"{salary_min}+"
                    
                    search_url = f"{self.base_url}/jobs?{urlencode(search_params)}"
                    
                    # Navigate to search results with random delay
                    await asyncio.sleep(random.uniform(2, 5))
                    await self.page.goto(search_url, wait_until="domcontentloaded")
                    await self.wait_between_requests()
                    
                    # Extract job listings
                    job_elements = await self.page.query_selector_all('[data-jk]')
                    
                    for job_element in job_elements[:max_results]:
                        try:
                            job_data = await self._extract_job_data(job_element, keyword, location)
                            if job_data:
                                jobs.append(job_data)
                                
                        except Exception as e:
                            print(f"Error extracting job data: {e}")
                            continue
                    
                    # Respect rate limits
                    await asyncio.sleep(random.uniform(3, 7))
                    
                    if len(jobs) >= max_results:
                        break
                
                if len(jobs) >= max_results:
                    break
                    
        except Exception as e:
            print(f"Indeed search failed: {e}")
            
        print(f"Indeed scraper found {len(jobs)} jobs")
        return jobs
    
    async def _extract_job_data(self, job_element, keyword: str, location: str) -> Optional[JobData]:
        """Extract job data from a job element."""
        try:
            # Get job ID for URL
            job_id = await job_element.get_attribute('data-jk')
            if not job_id:
                return None
            
            # Extract basic info
            title_element = await job_element.query_selector('h2 a span')
            title = await title_element.text_content() if title_element else "Unknown Title"
            
            company_element = await job_element.query_selector('[data-testid="company-name"]')
            company = await company_element.text_content() if company_element else "Unknown Company"
            
            location_element = await job_element.query_selector('[data-testid="job-location"]')
            job_location = await location_element.text_content() if location_element else location
            
            # Extract salary if available
            salary_element = await job_element.query_selector('[data-testid="attribute_snippet_testid"]')
            salary_text = await salary_element.text_content() if salary_element else ""
            salary_min, salary_max = self.parse_salary(salary_text)
            
            # Extract snippet/description
            snippet_element = await job_element.query_selector('[data-testid="job-snippet"]')
            snippet = await snippet_element.text_content() if snippet_element else ""
            
            # Build job URLs
            job_url = f"{self.base_url}/viewjob?jk={job_id}"
            
            # Determine job type
            job_type = self.extract_job_type(f"{title} {snippet}")
            
            # Create job data
            job_data = JobData(
                title=title.strip(),
                company=company.strip(),
                location=job_location.strip(),
                description=snippet.strip(),
                requirements=f"Keyword match: {keyword}",
                benefits="See job posting for details",
                salary_min=salary_min,
                salary_max=salary_max,
                job_type=job_type,
                application_url=job_url,
                application_email=None,
                external_id=job_id,
                external_url=job_url,
                posted_date=datetime.utcnow() - timedelta(days=random.randint(1, 14)),
                source="indeed"
            )
            
            return job_data
            
        except Exception as e:
            print(f"Error extracting job data: {e}")
            return None
    
    async def get_job_details(self, job_url: str) -> Optional[JobData]:
        """Get detailed job information."""
        try:
            await self.page.goto(job_url, wait_until="domcontentloaded")
            await self.wait_between_requests()
            
            # Extract detailed job information
            title_element = await self.page.query_selector('h1')
            title = await title_element.text_content() if title_element else "Unknown Title"
            
            company_element = await self.page.query_selector('[data-testid="inlineHeader-companyName"]')
            company = await company_element.text_content() if company_element else "Unknown Company"
            
            location_element = await self.page.query_selector('[data-testid="inlineHeader-companyLocation"]')
            location = await location_element.text_content() if location_element else "Unknown Location"
            
            description_element = await self.page.query_selector('#jobDescriptionText')
            description = await description_element.text_content() if description_element else ""
            
            # Extract job ID from URL
            job_id = job_url.split('jk=')[-1].split('&')[0] if 'jk=' in job_url else ""
            
            job_data = JobData(
                title=title.strip(),
                company=company.strip(),
                location=location.strip(),
                description=description.strip(),
                requirements="See job description",
                benefits="See job posting for details",
                salary_min=None,
                salary_max=None,
                job_type=self.extract_job_type(f"{title} {description}"),
                application_url=job_url,
                application_email=None,
                external_id=job_id,
                external_url=job_url,
                posted_date=datetime.utcnow(),
                source="indeed"
            )
            
            return job_data
            
        except Exception as e:
            print(f"Error getting job details: {e}")
            return None 