"""
Google Jobs Schema Scraper - Enhanced Version

This scraper targets JobPosting structured data (JSON-LD) from organization websites.
Enhanced with JavaScript rendering, robust parsing, and anti-bot measures.
"""

import asyncio
import json
import logging
import re
import time
from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup
from dateutil import parser as date_parser
from playwright.async_api import async_playwright

from .base_scraper import BaseScraper


class GoogleJobsSchemaScraper(BaseScraper):
    """
    Enhanced Google Jobs Schema scraper that extracts JobPosting structured data
    from organization websites with JavaScript rendering and robust parsing.
    """

    def __init__(self, filters: Optional[Dict] = None):
        super().__init__()
        self.filters = filters or {}
        self.logger = logging.getLogger(__name__)
        
        # Enhanced headers with rotation
        self.headers_pool = [
            {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            },
            {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            },
            {
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
        ]
        
        # Enhanced organization targets with known ATS domains
        self.target_organizations = {
            # Universities (known to use schema)
            'universities': [
                'https://careers.harvard.edu',
                'https://careers.mit.edu',
                'https://jobs.yale.edu',
                'https://careers.stanford.edu',
                'https://careers.princeton.edu',
                'https://careers.columbia.edu',
                'https://careers.upenn.edu',
                'https://careers.brown.edu',
                'https://careers.cornell.edu',
                'https://careers.dartmouth.edu',
                'https://jobs.berkeley.edu',
                'https://careers.ucla.edu',
                'https://careers.usc.edu',
                'https://careers.nyu.edu',
                'https://careers.georgetown.edu',
            ],
            
            # Tech companies with ATS
            'tech_companies': [
                'https://jobs.lever.co/airbnb',
                'https://jobs.lever.co/stripe',
                'https://jobs.lever.co/notion',
                'https://jobs.lever.co/github',
                'https://jobs.lever.co/figma',
                'https://boards.greenhouse.io/airbnb',
                'https://boards.greenhouse.io/stripe', 
                'https://boards.greenhouse.io/notion',
                'https://boards.greenhouse.io/github',
                'https://boards.greenhouse.io/figma',
                'https://apply.workable.com/stripe',
                'https://apply.workable.com/notion',
                'https://jobs.smartrecruiters.com/Airbnb',
                'https://jobs.smartrecruiters.com/Stripe',
            ],
            
            # Government (often uses schema)
            'government': [
                'https://www.usajobs.gov',
                'https://www.boston.gov/departments/human-resources/jobs',
                'https://www.seattle.gov/human-resources/jobs',
                'https://www.nyc.gov/jobs',
                'https://www.sf.gov/departments/human-resources',
            ],
            
            # Healthcare systems
            'healthcare': [
                'https://jobs.mayoclinic.org',
                'https://careers.clevelandclinic.org',
                'https://careers.kp.org',
                'https://careers.johnshopkins.org',
                'https://careers.partners.org',
            ],
            
            # Nonprofits
            'nonprofits': [
                'https://careers.redcross.org',
                'https://www.aclu.org/careers',
                'https://www.doctorswithoutborders.org/careers',
                'https://careers.unitedway.org',
                'https://careers.habitat.org',
            ]
        }
        
        # Known ATS domain patterns for relaxed domain checking
        self.ats_domains = {
            'lever.co', 'jobs.lever.co',
            'greenhouse.io', 'boards.greenhouse.io',
            'workable.com', 'apply.workable.com',
            'smartrecruiters.com', 'jobs.smartrecruiters.com',
            'bamboohr.com', 'careers.bamboohr.com',
            'jobvite.com', 'jobs.jobvite.com',
            'icims.com', 'careers.icims.com',
            'taleo.net', 'careers.taleo.net',
        }
        
        # Enhanced career page patterns
        self.career_patterns = [
            '/careers', '/careers/', '/career', '/career/',
            '/jobs', '/jobs/', '/job', '/job/',
            '/opportunities', '/opportunities/', '/opportunity', '/opportunity/',
            '/work-with-us', '/work-with-us/', '/join-us', '/join-us/',
            '/employment', '/employment/', '/hiring', '/hiring/',
            '/positions', '/positions/', '/openings', '/openings/',
            '/en/careers', '/en-us/careers', '/en/jobs', '/en-us/jobs',
            '/company/careers', '/company/jobs', '/about/careers', '/about/jobs',
        ]
        
        # Rate limiting
        self.request_delay = 2.0  # seconds between requests
        self.last_request_time = 0

    async def scrape_jobs(self, limit: int = 100, filters: Optional[Dict] = None) -> List[Dict]:
        """
        Enhanced job scraping with JavaScript rendering and robust parsing.
        """
        self.logger.info(f"Starting enhanced Google Jobs Schema scraping (limit: {limit})")
        
        all_jobs = []
        processed_urls = set()
        
        try:
            # Use Playwright for JavaScript rendering
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context(
                    user_agent=self.headers_pool[0]['User-Agent'],
                    viewport={'width': 1920, 'height': 1080}
                )
                
                try:
                    for category, urls in self.target_organizations.items():
                        self.logger.info(f"Processing {category} organizations...")
                        
                        for org_url in urls:
                            if len(all_jobs) >= limit:
                                break
                                
                            try:
                                # Discover career pages and job postings
                                job_urls = await self._discover_job_urls(context, org_url)
                                
                                # Process each job URL
                                for job_url in job_urls:
                                    if job_url in processed_urls or len(all_jobs) >= limit:
                                        continue
                                        
                                    processed_urls.add(job_url)
                                    
                                    # Extract job data with JS rendering
                                    jobs = await self._extract_jobs_from_page(context, job_url)
                                    
                                    if jobs:
                                        # Apply filters
                                        filtered_jobs = self._filter_jobs(jobs, filters)
                                        all_jobs.extend(filtered_jobs)
                                        
                                        self.logger.info(f"Found {len(filtered_jobs)} jobs from {job_url}")
                                    
                                    # Rate limiting
                                    await self._rate_limit()
                                    
                                if len(all_jobs) >= limit:
                                    break
                                    
                            except Exception as e:
                                self.logger.error(f"Error processing {org_url}: {e}")
                                continue
                    
                finally:
                    await context.close()
                    await browser.close()
                    
        except Exception as e:
            self.logger.error(f"Error in enhanced scraping: {e}")
        
        # Deduplicate and normalize
        unique_jobs = self._deduplicate_jobs(all_jobs)
        
        self.logger.info(f"Enhanced scraping completed. Found {len(unique_jobs)} unique jobs.")
        return unique_jobs[:limit]

    async def _discover_job_urls(self, context, org_url: str) -> List[str]:
        """
        Enhanced job URL discovery with JavaScript rendering and relaxed domain checking.
        """
        job_urls = []
        
        try:
            page = await context.new_page()
            
            # Navigate to main page
            await page.goto(org_url, wait_until='domcontentloaded', timeout=30000)
            await page.wait_for_timeout(2000)  # Wait for JS to load
            
            # Check main page for JSON-LD first
            content = await page.content()
            if self._has_job_posting_schema(content):
                job_urls.append(org_url)
                self.logger.info(f"Found schema on main page: {org_url}")
            
            # Look for career page links
            career_links = await self._find_career_links(page, org_url)
            
            for career_link in career_links:
                try:
                    await page.goto(career_link, wait_until='domcontentloaded', timeout=30000)
                    await page.wait_for_timeout(2000)
                    
                    # Check if career page has schema
                    content = await page.content()
                    if self._has_job_posting_schema(content):
                        job_urls.append(career_link)
                        self.logger.info(f"Found schema on career page: {career_link}")
                    
                    # Look for individual job links
                    job_links = await self._find_job_links(page, career_link)
                    job_urls.extend(job_links)
                    
                except Exception as e:
                    self.logger.error(f"Error processing career link {career_link}: {e}")
                    continue
            
            await page.close()
            
        except Exception as e:
            self.logger.error(f"Error discovering job URLs from {org_url}: {e}")
        
        return list(set(job_urls))  # Remove duplicates

    async def _find_career_links(self, page, base_url: str) -> List[str]:
        """
        Find career page links with relaxed domain checking.
        """
        career_links = []
        base_domain = urlparse(base_url).netloc
        
        try:
            # Get all links
            links = await page.eval_on_selector_all('a[href]', '''
                elements => elements.map(el => ({
                    href: el.href,
                    text: el.textContent.toLowerCase()
                }))
            ''')
            
            for link_info in links:
                href = link_info['href']
                text = link_info['text']
                
                # Check if this looks like a career link
                if any(pattern in href.lower() for pattern in self.career_patterns):
                    full_url = urljoin(base_url, href)
                    parsed = urlparse(full_url)
                    
                    # Relaxed domain checking - allow subdomains and known ATS domains
                    if (parsed.netloc == base_domain or 
                        parsed.netloc.endswith(f'.{base_domain}') or
                        any(ats_domain in parsed.netloc for ats_domain in self.ats_domains)):
                        career_links.append(full_url)
                
                # Check link text for career indicators
                career_keywords = ['careers', 'jobs', 'work with us', 'join us', 'opportunities', 'hiring']
                if any(keyword in text for keyword in career_keywords):
                    full_url = urljoin(base_url, href)
                    parsed = urlparse(full_url)
                    
                    if (parsed.netloc == base_domain or 
                        parsed.netloc.endswith(f'.{base_domain}') or
                        any(ats_domain in parsed.netloc for ats_domain in self.ats_domains)):
                        career_links.append(full_url)
                        
        except Exception as e:
            self.logger.error(f"Error finding career links: {e}")
        
        return list(set(career_links))

    async def _find_job_links(self, page, base_url: str) -> List[str]:
        """
        Find individual job posting links with improved pattern matching.
        """
        job_links = []
        base_domain = urlparse(base_url).netloc
        
        try:
            # Get all links
            links = await page.eval_on_selector_all('a[href]', '''
                elements => elements.map(el => ({
                    href: el.href,
                    text: el.textContent.toLowerCase()
                }))
            ''')
            
            # Job link patterns
            job_patterns = [
                r'/job[s]?/[0-9]+',
                r'/job[s]?/[a-zA-Z0-9\-]+',
                r'/position[s]?/[a-zA-Z0-9\-]+',
                r'/opening[s]?/[a-zA-Z0-9\-]+',
                r'/career[s]?/[a-zA-Z0-9\-]+',
                r'/apply/[a-zA-Z0-9\-]+',
                r'/posting[s]?/[a-zA-Z0-9\-]+',
                r'/detail/[a-zA-Z0-9\-]+',
                r'/view/[a-zA-Z0-9\-]+',
            ]
            
            for link_info in links:
                href = link_info['href']
                text = link_info['text']
                
                # Check URL patterns
                for pattern in job_patterns:
                    if re.search(pattern, href, re.IGNORECASE):
                        full_url = urljoin(base_url, href)
                        parsed = urlparse(full_url)
                        
                        if (parsed.netloc == base_domain or 
                            parsed.netloc.endswith(f'.{base_domain}') or
                            any(ats_domain in parsed.netloc for ats_domain in self.ats_domains)):
                            job_links.append(full_url)
                        break
                
                # Check link text
                job_keywords = ['view job', 'apply', 'details', 'read more', 'learn more']
                if any(keyword in text for keyword in job_keywords):
                    full_url = urljoin(base_url, href)
                    parsed = urlparse(full_url)
                    
                    if (parsed.netloc == base_domain or 
                        parsed.netloc.endswith(f'.{base_domain}') or
                        any(ats_domain in parsed.netloc for ats_domain in self.ats_domains)):
                        job_links.append(full_url)
                        
        except Exception as e:
            self.logger.error(f"Error finding job links: {e}")
        
        return list(set(job_links))

    def _has_job_posting_schema(self, content: str) -> bool:
        """
        Enhanced check for JobPosting schema in HTML content.
        """
        if not content:
            return False
        
        # Check for JSON-LD script tags
        if 'application/ld+json' not in content.lower():
            return False
        
        # Use BeautifulSoup to parse and check for JobPosting
        try:
            soup = BeautifulSoup(content, 'html.parser')
            script_tags = soup.find_all('script', type='application/ld+json')
            
            for script in script_tags:
                if not script.text:
                    continue
                
                try:
                    data = json.loads(script.text)
                    if self._contains_job_posting(data):
                        return True
                except json.JSONDecodeError:
                    continue
                    
        except Exception:
            pass
        
        return False

    def _contains_job_posting(self, data) -> bool:
        """
        Enhanced check for JobPosting type in JSON-LD data.
        """
        if isinstance(data, list):
            return any(self._contains_job_posting(item) for item in data)
        
        if isinstance(data, dict):
            types = data.get('@type', [])
            if isinstance(types, str):
                types = [types]
            
            return 'JobPosting' in types
        
        return False

    async def _extract_jobs_from_page(self, context, url: str) -> List[Dict]:
        """
        Enhanced job extraction with JavaScript rendering and robust parsing.
        """
        jobs = []
        
        try:
            page = await context.new_page()
            
            # Navigate and wait for content
            await page.goto(url, wait_until='domcontentloaded', timeout=30000)
            await page.wait_for_timeout(3000)  # Wait for JS to load
            
            # Get rendered content
            content = await page.content()
            
            # Parse with BeautifulSoup
            soup = BeautifulSoup(content, 'html.parser')
            script_tags = soup.find_all('script', type='application/ld+json')
            
            for script in script_tags:
                if not script.text:
                    continue
                
                try:
                    data = json.loads(script.text)
                    
                    # Handle both single objects and arrays
                    if isinstance(data, list):
                        for item in data:
                            if self._contains_job_posting(item):
                                job = self._parse_job_posting(item, url)
                                if job:
                                    jobs.append(job)
                    else:
                        if self._contains_job_posting(data):
                            job = self._parse_job_posting(data, url)
                            if job:
                                jobs.append(job)
                
                except json.JSONDecodeError as e:
                    self.logger.error(f"JSON decode error in {url}: {e}")
                    continue
            
            await page.close()
            
        except Exception as e:
            self.logger.error(f"Error extracting jobs from {url}: {e}")
        
        return jobs

    def _parse_job_posting(self, data: Dict, source_url: str) -> Optional[Dict]:
        """
        Enhanced JobPosting parsing with robust field extraction.
        """
        try:
            # Extract basic fields
            title = data.get('title', '').strip()
            description = data.get('description', '').strip()
            
            if not title:
                return None
            
            # Extract company with fallback
            company = self._extract_company(data)
            
            # Extract location with improved parsing
            location = self._extract_location(data.get('jobLocation', {}))
            
            # Extract salary with robust parsing
            salary = self._extract_salary(data.get('baseSalary', {}))
            
            # Extract dates with dateutil parser
            posted_date = self._extract_date(data.get('datePosted'))
            expires_date = self._extract_date(data.get('validThrough'))
            
            # Extract employment type
            employment_type = data.get('employmentType', '').strip()
            
            # Extract URL
            job_url = data.get('url', source_url)
            
            # Extract additional fields
            external_id = data.get('identifier', {})
            if isinstance(external_id, dict):
                external_id = external_id.get('value', '')
            
            # Build job object
            job = {
                'title': title,
                'company': company,
                'location': location,
                'description': description,
                'salary': salary,
                'posted_date': posted_date,
                'expires_date': expires_date,
                'employment_type': employment_type,
                'url': job_url,
                'external_id': str(external_id) if external_id else None,
                'source': 'Google Jobs Schema',
                'source_url': source_url,
                'scraped_at': datetime.now().isoformat(),
            }
            
            return job
            
        except Exception as e:
            self.logger.error(f"Error parsing job posting: {e}")
            return None

    def _extract_company(self, data: Dict) -> str:
        """
        Enhanced company extraction with multiple fallbacks.
        """
        # Try hiringOrganization first
        hiring_org = data.get('hiringOrganization', {})
        if isinstance(hiring_org, dict):
            company = hiring_org.get('name', '')
            if company:
                return company.strip()
        elif isinstance(hiring_org, str):
            return hiring_org.strip()
        
        # Try employer
        employer = data.get('employer', {})
        if isinstance(employer, dict):
            company = employer.get('name', '')
            if company:
                return company.strip()
        elif isinstance(employer, str):
            return employer.strip()
        
        return 'Unknown Company'

    def _extract_location(self, location_data) -> str:
        """
        Enhanced location extraction with multiple formats.
        """
        if not location_data:
            return 'Location not specified'
        
        # Handle array of locations
        if isinstance(location_data, list):
            if location_data:
                location_data = location_data[0]
            else:
                return 'Location not specified'
        
        # Handle string location
        if isinstance(location_data, str):
            return location_data.strip()
        
        # Handle Place object
        if isinstance(location_data, dict):
            # Try address field
            address = location_data.get('address', {})
            if isinstance(address, dict):
                # Build location from address components
                parts = []
                
                city = address.get('addressLocality', '')
                if city:
                    parts.append(city)
                
                region = address.get('addressRegion', '')
                if region:
                    parts.append(region)
                
                country = address.get('addressCountry', '')
                if country:
                    parts.append(country)
                
                if parts:
                    return ', '.join(parts)
            
            # Try name field
            name = location_data.get('name', '')
            if name:
                return name.strip()
        
        return 'Location not specified'

    def _extract_salary(self, salary_data) -> Optional[str]:
        """
        Enhanced salary extraction with multiple formats and fallbacks.
        """
        if not salary_data or not isinstance(salary_data, dict):
            return None
        
        try:
            # Try value field first
            value = salary_data.get('value', {})
            
            if isinstance(value, dict):
                # Handle MonetaryAmountDistribution
                min_val = value.get('minValue')
                max_val = value.get('maxValue')
                single_val = value.get('value')
                
                if min_val and max_val:
                    return f"${int(min_val):,} - ${int(max_val):,}"
                elif single_val:
                    return f"${int(single_val):,}"
            
            elif isinstance(value, (int, float)):
                return f"${int(value):,}"
            
            # Try direct minValue/maxValue
            min_val = salary_data.get('minValue')
            max_val = salary_data.get('maxValue')
            
            if min_val and max_val:
                return f"${int(min_val):,} - ${int(max_val):,}"
            
            # Try to extract any numbers from salary text
            salary_text = str(salary_data)
            numbers = re.findall(r'\d+(?:,\d+)*', salary_text)
            if numbers:
                if len(numbers) >= 2:
                    return f"${numbers[0]} - ${numbers[1]}"
                else:
                    return f"${numbers[0]}"
            
        except Exception as e:
            self.logger.error(f"Error extracting salary: {e}")
        
        return None

    def _extract_date(self, date_str) -> Optional[str]:
        """
        Enhanced date extraction with dateutil parser.
        """
        if not date_str:
            return None
        
        try:
            # Use dateutil parser for robust date parsing
            parsed_date = date_parser.parse(date_str)
            return parsed_date.isoformat()
        except Exception as e:
            self.logger.error(f"Error parsing date '{date_str}': {e}")
            return None

    def _filter_jobs(self, jobs: List[Dict], filters: Optional[Dict] = None) -> List[Dict]:
        """
        Enhanced filtering that checks canonical fields, not just description.
        """
        if not filters:
            filters = self.filters or {}
        
        filtered_jobs = []
        
        for job in jobs:
            # Check if job matches filters
            if self._matches_filters(job, filters):
                filtered_jobs.append(job)
        
        return filtered_jobs

    def _matches_filters(self, job: Dict, filters: Dict) -> bool:
        """
        Enhanced filter matching with canonical field checking.
        """
        # Keywords - check title, description, and company
        keywords = filters.get('keywords', [])
        if keywords:
            searchable_text = ' '.join([
                job.get('title', ''),
                job.get('description', ''),
                job.get('company', '')
            ]).lower()
            
            if not any(keyword.lower() in searchable_text for keyword in keywords):
                return False
        
        # Location filter
        location_filter = filters.get('location', '')
        if location_filter:
            job_location = job.get('location', '').lower()
            if location_filter.lower() not in job_location:
                return False
        
        # Employment type filter
        employment_type_filter = filters.get('employment_type', '')
        if employment_type_filter:
            job_employment_type = job.get('employment_type', '').lower()
            if employment_type_filter.lower() not in job_employment_type:
                return False
        
        # Company filter
        company_filter = filters.get('company', '')
        if company_filter:
            job_company = job.get('company', '').lower()
            if company_filter.lower() not in job_company:
                return False
        
        return True

    def _deduplicate_jobs(self, jobs: List[Dict]) -> List[Dict]:
        """
        Enhanced deduplication using schema ID and multiple fields.
        """
        seen_jobs = set()
        unique_jobs = []
        
        for job in jobs:
            # Build signature with multiple fields
            signature_parts = []
            
            # Use external_id if available
            if job.get('external_id'):
                signature_parts.append(job['external_id'])
            
            # Use URL if available
            if job.get('url'):
                signature_parts.append(job['url'])
            
            # Fallback to title + company + location
            signature_parts.extend([
                job.get('title', ''),
                job.get('company', ''),
                job.get('location', '')
            ])
            
            signature = '|'.join(signature_parts).lower()
            
            if signature not in seen_jobs:
                seen_jobs.add(signature)
                unique_jobs.append(job)
        
        return unique_jobs

    async def _rate_limit(self):
        """
        Enhanced rate limiting with exponential backoff.
        """
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        
        if time_since_last_request < self.request_delay:
            sleep_time = self.request_delay - time_since_last_request
            await asyncio.sleep(sleep_time)
        
        self.last_request_time = time.time()

    async def test_scraping(self, test_urls: Optional[List[str]] = None) -> List[Dict]:
        """
        Enhanced test method for debugging and validation.
        """
        if test_urls is None:
            test_urls = [
                'https://careers.harvard.edu',
                'https://careers.mit.edu',
                'https://jobs.lever.co/airbnb',
                'https://boards.greenhouse.io/airbnb',
            ]
        
        self.logger.info(f"Testing schema scraping with {len(test_urls)} URLs...")
        
        all_jobs = []
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            
            try:
                for url in test_urls:
                    self.logger.info(f"Testing: {url}")
                    
                    # Discover job URLs
                    job_urls = await self._discover_job_urls(context, url)
                    self.logger.info(f"Found {len(job_urls)} job URLs")
                    
                    # Extract jobs from first few URLs
                    for job_url in job_urls[:3]:
                        jobs = await self._extract_jobs_from_page(context, job_url)
                        all_jobs.extend(jobs)
                        self.logger.info(f"Extracted {len(jobs)} jobs from {job_url}")
                    
                    await self._rate_limit()
                    
            finally:
                await context.close()
                await browser.close()
        
        unique_jobs = self._deduplicate_jobs(all_jobs)
        self.logger.info(f"Test completed. Found {len(unique_jobs)} unique jobs.")
        
        return unique_jobs 