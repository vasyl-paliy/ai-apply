"""LinkedIn job scraper implementation."""

import re
from typing import List, Optional
from urllib.parse import urlencode, quote
from datetime import datetime, timedelta

from loguru import logger

from .base_scraper import BaseScraper, JobData
from ..app.config import settings


class LinkedInScraper(BaseScraper):
    """LinkedIn job scraper."""
    
    def __init__(self):
        super().__init__()
        self.base_url = "https://www.linkedin.com"
        self.jobs_url = f"{self.base_url}/jobs/search"
        
    async def login(self) -> bool:
        """Login to LinkedIn if credentials are provided."""
        if not settings.linkedin_email or not settings.linkedin_password:
            logger.warning("LinkedIn credentials not provided, proceeding without login")
            return False
            
        try:
            await self.page.goto(f"{self.base_url}/login")
            await self.page.wait_for_load_state("networkidle")
            
            # Fill login form
            await self.safe_fill("#username", settings.linkedin_email)
            await self.safe_fill("#password", settings.linkedin_password)
            
            # Click login button
            await self.safe_click("button[type='submit']")
            await self.page.wait_for_load_state("networkidle")
            
            # Check if login was successful
            current_url = self.page.url
            if "feed" in current_url or "mynetwork" in current_url:
                logger.info("Successfully logged into LinkedIn")
                return True
            else:
                logger.warning("LinkedIn login may have failed")
                return False
                
        except Exception as e:
            logger.error(f"Failed to login to LinkedIn: {e}")
            return False
            
    def build_search_url(
        self,
        keywords: List[str],
        locations: List[str],
        job_types: Optional[List[str]] = None,
        salary_min: Optional[int] = None
    ) -> str:
        """Build LinkedIn job search URL."""
        params = {
            'keywords': ' '.join(keywords),
            'location': locations[0] if locations else '',
            'f_TPR': 'r86400',  # Posted in last 24 hours
            'f_JT': self._map_job_types(job_types) if job_types else '',
            'start': 0
        }
        
        # Add salary filter if provided
        if salary_min:
            # LinkedIn salary ranges (approximate mapping)
            if salary_min >= 100000:
                params['f_SB2'] = '4'  # $100k+
            elif salary_min >= 80000:
                params['f_SB2'] = '3'  # $80k-$100k
            elif salary_min >= 60000:
                params['f_SB2'] = '2'  # $60k-$80k
            elif salary_min >= 40000:
                params['f_SB2'] = '1'  # $40k-$60k
                
        # Remove empty parameters
        params = {k: v for k, v in params.items() if v}
        
        return f"{self.jobs_url}?{urlencode(params)}"
        
    def _map_job_types(self, job_types: List[str]) -> str:
        """Map job types to LinkedIn filter values."""
        type_mapping = {
            'full_time': 'F',
            'part_time': 'P',
            'contract': 'C',
            'internship': 'I',
            'remote': 'R'
        }
        
        linkedin_types = []
        for job_type in job_types:
            if job_type in type_mapping:
                linkedin_types.append(type_mapping[job_type])
                
        return ','.join(linkedin_types)
        
    async def search_jobs(
        self,
        keywords: List[str],
        locations: List[str],
        job_types: Optional[List[str]] = None,
        salary_min: Optional[int] = None,
        max_results: int = 50
    ) -> List[JobData]:
        """Search for jobs on LinkedIn."""
        jobs = []
        
        try:
            # Login first (optional but recommended)
            await self.login()
            
            # Build search URL
            search_url = self.build_search_url(keywords, locations, job_types, salary_min)
            logger.info(f"Searching LinkedIn with URL: {search_url}")
            
            await self.page.goto(search_url)
            await self.page.wait_for_load_state("networkidle")
            
            # Wait for job listings to load
            await self.page.wait_for_selector(".jobs-search__results-list", timeout=10000)
            
            page_count = 0
            max_pages = (max_results // 25) + 1  # LinkedIn shows ~25 jobs per page
            
            while len(jobs) < max_results and page_count < max_pages:
                # Get job cards on current page
                job_cards = await self.page.query_selector_all(".base-card")
                
                for card in job_cards:
                    if len(jobs) >= max_results:
                        break
                        
                    try:
                        job_data = await self._extract_job_from_card(card)
                        if job_data:
                            jobs.append(job_data)
                            
                    except Exception as e:
                        logger.warning(f"Failed to extract job from card: {e}")
                        continue
                        
                # Try to go to next page
                next_button = await self.page.query_selector("button[aria-label='Next']")
                if next_button and await next_button.is_enabled():
                    await next_button.click()
                    await self.page.wait_for_load_state("networkidle")
                    await self.wait_between_requests()
                    page_count += 1
                else:
                    break
                    
        except Exception as e:
            logger.error(f"Error searching LinkedIn jobs: {e}")
            
        return jobs
        
    async def _extract_job_from_card(self, card) -> Optional[JobData]:
        """Extract job data from a LinkedIn job card."""
        try:
            # Get job title and URL
            title_element = await card.query_selector(".base-search-card__title a")
            if not title_element:
                return None
                
            title = await title_element.text_content()
            job_url = await title_element.get_attribute("href")
            
            if not job_url.startswith("http"):
                job_url = self.base_url + job_url
                
            # Get company name
            company_element = await card.query_selector(".base-search-card__subtitle")
            company = await company_element.text_content() if company_element else "Unknown"
            
            # Get location
            location_element = await card.query_selector(".job-search-card__location")
            location = await location_element.text_content() if location_element else "Unknown"
            
            # Get posting date
            posted_element = await card.query_selector("time")
            posted_date = None
            if posted_element:
                datetime_attr = await posted_element.get_attribute("datetime")
                if datetime_attr:
                    posted_date = datetime.fromisoformat(datetime_attr.replace('Z', '+00:00'))
                    
            # Extract job ID from URL
            job_id_match = re.search(r'/view/(\d+)', job_url)
            external_id = job_id_match.group(1) if job_id_match else job_url
            
            # Get additional details by visiting the job page
            job_details = await self.get_job_details(job_url)
            
            return JobData(
                title=title.strip(),
                company=company.strip(),
                location=location.strip(),
                description=job_details.description if job_details else "",
                requirements=job_details.requirements if job_details else "",
                benefits=job_details.benefits if job_details else "",
                salary_min=job_details.salary_min if job_details else None,
                salary_max=job_details.salary_max if job_details else None,
                job_type=job_details.job_type if job_details else self.extract_job_type(title),
                application_url=job_url,
                application_email=None,  # LinkedIn typically doesn't show email
                external_id=external_id,
                external_url=job_url,
                posted_date=posted_date,
                source="linkedin"
            )
            
        except Exception as e:
            logger.warning(f"Failed to extract job data from card: {e}")
            return None
            
    async def get_job_details(self, job_url: str) -> Optional[JobData]:
        """Get detailed job information from job page."""
        try:
            # Create new page for job details to avoid disrupting search
            context = self.browser.contexts[0]
            detail_page = await context.new_page()
            
            await detail_page.goto(job_url)
            await detail_page.wait_for_load_state("networkidle")
            
            # Extract job description
            description = ""
            desc_element = await detail_page.query_selector(".show-more-less-html__markup")
            if desc_element:
                description = await desc_element.text_content()
                
            # Extract company info
            company_element = await detail_page.query_selector(".topcard__org-name-link")
            company = await company_element.text_content() if company_element else "Unknown"
            
            # Extract job title
            title_element = await detail_page.query_selector(".topcard__title")
            title = await title_element.text_content() if title_element else "Unknown"
            
            # Extract location
            location_element = await detail_page.query_selector(".topcard__flavor--bullet")
            location = await location_element.text_content() if location_element else "Unknown"
            
            # Try to extract salary information
            salary_min, salary_max = None, None
            salary_elements = await detail_page.query_selector_all("text*='$'")
            for element in salary_elements:
                text = await element.text_content()
                if '$' in text:
                    salary_min, salary_max = self.parse_salary(text)
                    break
                    
            # Parse job type from description
            job_type = self.extract_job_type(f"{title} {description}")
            
            # Split description into parts (rough estimation)
            description_parts = description.split('\n\n') if description else []
            requirements = ""
            benefits = ""
            
            if len(description_parts) > 1:
                # Try to identify requirements and benefits sections
                for part in description_parts:
                    part_lower = part.lower()
                    if any(word in part_lower for word in ['requirements', 'qualifications', 'experience']):
                        requirements = part
                    elif any(word in part_lower for word in ['benefits', 'perks', 'compensation']):
                        benefits = part
                        
            await detail_page.close()
            
            return JobData(
                title=title.strip(),
                company=company.strip(),
                location=location.strip(),
                description=description.strip(),
                requirements=requirements.strip(),
                benefits=benefits.strip(),
                salary_min=salary_min,
                salary_max=salary_max,
                job_type=job_type,
                application_url=job_url,
                application_email=None,
                external_id=job_url.split('/')[-1],
                external_url=job_url,
                posted_date=None,
                source="linkedin"
            )
            
        except Exception as e:
            logger.warning(f"Failed to get job details from {job_url}: {e}")
            return None 