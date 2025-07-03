"""Base scraper class for job sites."""

import asyncio
import time
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass

from playwright.async_api import async_playwright, Page, Browser
from loguru import logger

from ..app.config import settings


@dataclass
class JobData:
    """Structured job data."""
    title: str
    company: str
    location: str
    description: str
    requirements: str
    benefits: str
    salary_min: Optional[int]
    salary_max: Optional[int]
    job_type: str
    application_url: str
    application_email: Optional[str]
    external_id: str
    external_url: str
    posted_date: Optional[datetime]
    source: str


class BaseScraper(ABC):
    """Base class for job site scrapers."""
    
    def __init__(self):
        self.source_name = self.__class__.__name__.lower().replace('scraper', '')
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.jobs_scraped = 0
        self.session_start = None
        
    async def __aenter__(self):
        """Async context manager entry."""
        await self.setup_browser()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.cleanup()
        
    async def setup_browser(self):
        """Setup Playwright browser."""
        try:
            self.playwright = await async_playwright().start()
            
            # Launch browser with appropriate settings
            browser_args = {
                'headless': settings.playwright_headless,
                'timeout': settings.playwright_timeout,
                'args': [
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-blink-features=AutomationControlled'
                ]
            }
            
            self.browser = await self.playwright.chromium.launch(**browser_args)
            
            # Create context with realistic settings
            context = await self.browser.new_context(
                user_agent=settings.user_agent,
                viewport={'width': 1366, 'height': 768},
                extra_http_headers={
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                }
            )
            
            self.page = await context.new_page()
            
            # Add stealth techniques
            await self.page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined,
                });
            """)
            
            logger.info(f"Browser setup complete for {self.source_name}")
            
        except Exception as e:
            logger.error(f"Failed to setup browser for {self.source_name}: {e}")
            raise
            
    async def cleanup(self):
        """Cleanup browser resources."""
        try:
            if self.page:
                await self.page.close()
            if self.browser:
                await self.browser.close()
            if hasattr(self, 'playwright'):
                await self.playwright.stop()
            logger.info(f"Browser cleanup complete for {self.source_name}")
        except Exception as e:
            logger.warning(f"Error during cleanup for {self.source_name}: {e}")
            
    async def wait_between_requests(self):
        """Wait between requests to avoid being blocked."""
        await asyncio.sleep(settings.scraping_delay)
        
    async def safe_click(self, selector: str, timeout: int = 5000) -> bool:
        """Safely click an element."""
        try:
            await self.page.wait_for_selector(selector, timeout=timeout)
            await self.page.click(selector)
            return True
        except Exception as e:
            logger.warning(f"Failed to click {selector}: {e}")
            return False
            
    async def safe_fill(self, selector: str, text: str, timeout: int = 5000) -> bool:
        """Safely fill an input field."""
        try:
            await self.page.wait_for_selector(selector, timeout=timeout)
            await self.page.fill(selector, text)
            return True
        except Exception as e:
            logger.warning(f"Failed to fill {selector}: {e}")
            return False
            
    async def safe_get_text(self, selector: str, timeout: int = 5000) -> Optional[str]:
        """Safely get text from an element."""
        try:
            element = await self.page.wait_for_selector(selector, timeout=timeout)
            return await element.text_content()
        except Exception as e:
            logger.warning(f"Failed to get text from {selector}: {e}")
            return None
            
    async def safe_get_attribute(self, selector: str, attribute: str, timeout: int = 5000) -> Optional[str]:
        """Safely get attribute from an element."""
        try:
            element = await self.page.wait_for_selector(selector, timeout=timeout)
            return await element.get_attribute(attribute)
        except Exception as e:
            logger.warning(f"Failed to get {attribute} from {selector}: {e}")
            return None
            
    def parse_salary(self, salary_text: str) -> tuple[Optional[int], Optional[int]]:
        """Parse salary text to extract min and max values."""
        if not salary_text:
            return None, None
            
        import re
        
        # Remove common salary prefixes/suffixes
        clean_text = re.sub(r'[,$]', '', salary_text.lower())
        
        # Look for salary ranges
        range_match = re.search(r'(\d+)(?:k|\,000)?.*?(?:to|-|–).*?(\d+)(?:k|\,000)?', clean_text)
        if range_match:
            min_sal = int(range_match.group(1))
            max_sal = int(range_match.group(2))
            
            # Handle k notation
            if 'k' in clean_text or min_sal < 1000:
                min_sal *= 1000
                max_sal *= 1000
                
            return min_sal, max_sal
            
        # Look for single salary values
        single_match = re.search(r'(\d+)(?:k|\,000)?', clean_text)
        if single_match:
            salary = int(single_match.group(1))
            if 'k' in clean_text or salary < 1000:
                salary *= 1000
            return salary, salary
            
        return None, None
        
    def extract_job_type(self, job_text: str) -> str:
        """Extract job type from job description or title."""
        job_text_lower = job_text.lower()
        
        if any(term in job_text_lower for term in ['remote', 'work from home', 'wfh']):
            return 'remote'
        elif any(term in job_text_lower for term in ['hybrid', 'flexible']):
            return 'hybrid'
        elif any(term in job_text_lower for term in ['part-time', 'part time', 'pt']):
            return 'part_time'
        elif any(term in job_text_lower for term in ['contract', 'contractor', 'freelance']):
            return 'contract'
        elif any(term in job_text_lower for term in ['intern', 'internship']):
            return 'internship'
        else:
            return 'full_time'
            
    @abstractmethod
    async def search_jobs(
        self,
        keywords: List[str],
        locations: List[str],
        job_types: Optional[List[str]] = None,
        salary_min: Optional[int] = None,
        max_results: int = 50
    ) -> List[JobData]:
        """Search for jobs. Must be implemented by subclasses."""
        pass
        
    @abstractmethod
    async def get_job_details(self, job_url: str) -> Optional[JobData]:
        """Get detailed job information. Must be implemented by subclasses."""
        pass
        
    async def scrape_jobs(
        self,
        keywords: List[str],
        locations: List[str],
        job_types: Optional[List[str]] = None,
        salary_min: Optional[int] = None,
        max_results: int = 50
    ) -> List[JobData]:
        """Main scraping method."""
        self.session_start = time.time()
        logger.info(f"Starting job scrape for {self.source_name} with keywords: {keywords}")
        
        try:
            jobs = await self.search_jobs(
                keywords=keywords,
                locations=locations,
                job_types=job_types,
                salary_min=salary_min,
                max_results=max_results
            )
            
            self.jobs_scraped = len(jobs)
            duration = time.time() - self.session_start
            
            logger.info(
                f"Scraping complete for {self.source_name}: "
                f"{self.jobs_scraped} jobs in {duration:.2f}s"
            )
            
            return jobs
            
        except Exception as e:
            logger.error(f"Error during scraping for {self.source_name}: {e}")
            raise 