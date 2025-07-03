"""
Google Jobs Schema Scraper - Extract structured job data from company websites.
This scraper targets JSON-LD structured data that companies embed for SEO purposes.
"""

import asyncio
import json
import re
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Set
from urllib.parse import urljoin, urlparse
import httpx
from bs4 import BeautifulSoup
from .base_scraper import BaseScraper, JobData


class SchemaScraper(BaseScraper):
    """Scraper for Google Jobs Schema (JSON-LD structured data)."""
    
    def __init__(self):
        super().__init__()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        # Common career page patterns
        self.career_paths = [
            '/careers', '/jobs', '/career', '/work-with-us', '/join-us',
            '/employment', '/opportunities', '/hiring', '/positions',
            '/careers/', '/jobs/', '/career/', '/work-with-us/', '/join-us/'
        ]
        
        # Job posting URL patterns
        self.job_patterns = [
            r'/job/[^/]+',
            r'/jobs/[^/]+',
            r'/career/[^/]+',
            r'/careers/[^/]+',
            r'/position/[^/]+',
            r'/apply/[^/]+',
            r'/job-posting/[^/]+',
            r'/job-\d+',
            r'/jobs-\d+',
        ]
    
    async def setup_browser(self):
        """Schema scraper doesn't need a browser - uses httpx."""
        print("Schema scraper setup - using httpx instead of browser")
        return True

    async def cleanup(self):
        """Schema scraper doesn't need cleanup."""
        print("Schema scraper cleanup - no browser to close")
        return True
    
    async def login(self):
        """No login required for schema scraping."""
        print("Schema scraper initialized - no login required")
        return True
    
    async def search_jobs(
        self,
        keywords: List[str],
        locations: List[str],
        job_types: Optional[List[str]] = None,
        salary_min: Optional[int] = None,
        max_results: int = 50
    ) -> List[JobData]:
        """Search for jobs using schema scraping."""
        
        # Get target websites to scrape
        target_sites = await self._find_target_sites(keywords, locations)
        
        all_jobs = []
        processed_urls = set()
        
        print(f"Found {len(target_sites)} target sites to scrape")
        
        async with httpx.AsyncClient(headers=self.headers, timeout=30) as client:
            for site in target_sites:
                try:
                    print(f"Scraping {site}...")
                    
                    # Find job pages on this site
                    job_urls = await self._find_job_pages(client, site)
                    
                    # Extract jobs from each page
                    for job_url in job_urls:
                        if job_url in processed_urls:
                            continue
                            
                        processed_urls.add(job_url)
                        
                        try:
                            job_data = await self._extract_job_from_page(client, job_url)
                            if job_data and self._matches_criteria(job_data, keywords, locations):
                                all_jobs.append(job_data)
                                print(f"Found job: {job_data.title} at {job_data.company}")
                                
                                if len(all_jobs) >= max_results:
                                    break
                        except Exception as e:
                            print(f"Error extracting job from {job_url}: {e}")
                            continue
                        
                        # Be respectful - small delay between requests
                        await asyncio.sleep(1)
                    
                    if len(all_jobs) >= max_results:
                        break
                        
                except Exception as e:
                    print(f"Error scraping site {site}: {e}")
                    continue
        
        print(f"Schema scraper found {len(all_jobs)} jobs")
        return all_jobs[:max_results]
    
    async def _find_target_sites(self, keywords: List[str], locations: List[str]) -> List[str]:
        """Find target websites that likely have job postings with schema."""
        
        # Start with some known good sites (you can expand this)
        known_sites = [
            # Tech companies
            'https://greenhouse.io',
            'https://lever.co',
            'https://workable.com',
            
            # Universities (often have good schema)
            'https://brown.edu',
            'https://harvard.edu',
            'https://mit.edu',
            'https://stanford.edu',
            
            # Nonprofits
            'https://redcross.org',
            'https://unitedway.org',
            
            # Local organizations (you can customize this for your area)
            'https://risd.edu',
            'https://jwu.edu',
        ]
        
        # You could also use Google search to find more sites
        # For now, let's use the known good ones
        return known_sites
    
    async def _find_job_pages(self, client: httpx.AsyncClient, base_url: str) -> List[str]:
        """Find job posting pages on a website."""
        
        job_urls = []
        
        try:
            # First, try to find the careers page
            careers_url = await self._find_careers_page(client, base_url)
            
            if careers_url:
                # Get the careers page content
                response = await client.get(careers_url)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Find all links that might be job postings
                    for link in soup.find_all('a', href=True):
                        try:
                            href = str(link.get('href', ''))
                            if not href:
                                continue
                            
                            # Convert relative URLs to absolute
                            if href.startswith('/'):
                                href = urljoin(base_url, href)
                            elif not href.startswith('http'):
                                continue
                            
                            # Check if this looks like a job posting URL
                            if any(re.search(pattern, href) for pattern in self.job_patterns):
                                job_urls.append(href)
                        except Exception:
                            continue
                    
                    # Also look for job links by text content
                    for link in soup.find_all('a', href=True):
                        try:
                            link_text = link.get_text().lower()
                            if any(keyword in link_text for keyword in ['apply', 'job', 'position', 'career', 'opening']):
                                href = str(link.get('href', ''))
                                if not href:
                                    continue
                                
                                if href.startswith('/'):
                                    href = urljoin(base_url, href)
                                elif href.startswith('http'):
                                    job_urls.append(href)
                        except Exception:
                            continue
        
        except Exception as e:
            print(f"Error finding job pages on {base_url}: {e}")
        
        # Remove duplicates and limit
        unique_urls = list(set(job_urls))[:20]  # Limit to 20 job pages per site
        return unique_urls
    
    async def _find_careers_page(self, client: httpx.AsyncClient, base_url: str) -> Optional[str]:
        """Find the careers page for a website."""
        
        for path in self.career_paths:
            try:
                careers_url = urljoin(base_url, path)
                response = await client.head(careers_url)
                
                if response.status_code == 200:
                    return careers_url
                    
            except Exception:
                continue
        
        return None
    
    async def _extract_job_from_page(self, client: httpx.AsyncClient, url: str) -> Optional[JobData]:
        """Extract job data from a single job posting page."""
        
        try:
            response = await client.get(url)
            if response.status_code != 200:
                return None
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find JSON-LD script tags
            script_tags = soup.find_all('script', type='application/ld+json')
            
            for script in script_tags:
                try:
                    if not script.string:
                        continue
                        
                    # Parse the JSON
                    json_data = json.loads(script.string)
                    
                    # Handle both single objects and arrays
                    if isinstance(json_data, list):
                        for item in json_data:
                            job_data = self._parse_job_schema(item, url)
                            if job_data:
                                return job_data
                    else:
                        job_data = self._parse_job_schema(json_data, url)
                        if job_data:
                            return job_data
                            
                except json.JSONDecodeError:
                    continue
                except Exception as e:
                    print(f"Error parsing JSON-LD: {e}")
                    continue
            
            # If no structured data found, try basic HTML parsing as fallback
            return self._extract_job_from_html(soup, url)
            
        except Exception as e:
            print(f"Error extracting job from {url}: {e}")
            return None
    
    def _parse_job_schema(self, schema_data: Dict[str, Any], url: str) -> Optional[JobData]:
        """Parse a job posting from JSON-LD schema."""
        
        # Check if this is a JobPosting schema
        schema_type = schema_data.get('@type', '')
        if schema_type != 'JobPosting':
            return None
        
        try:
            # Extract basic information
            title = schema_data.get('title', '')
            description = schema_data.get('description', '')
            
            # Extract company information
            hiring_org = schema_data.get('hiringOrganization', {})
            if isinstance(hiring_org, dict):
                company = hiring_org.get('name', '')
            else:
                company = str(hiring_org)
            
            # Extract location
            job_location = schema_data.get('jobLocation', {})
            if isinstance(job_location, dict):
                address = job_location.get('address', {})
                if isinstance(address, dict):
                    city = address.get('addressLocality', '')
                    state = address.get('addressRegion', '')
                    country = address.get('addressCountry', '')
                    location = f"{city}, {state}, {country}".strip(', ')
                else:
                    location = str(address)
            else:
                location = str(job_location)
            
            # Extract salary
            salary_info = schema_data.get('baseSalary', {})
            salary_min = None
            salary_max = None
            
            if isinstance(salary_info, dict):
                value = salary_info.get('value', {})
                if isinstance(value, dict):
                    min_val = value.get('minValue')
                    max_val = value.get('maxValue')
                    salary_min = int(min_val) if min_val is not None and isinstance(min_val, (int, float)) else None
                    salary_max = int(max_val) if max_val is not None and isinstance(max_val, (int, float)) else None
                elif isinstance(value, (int, float)):
                    salary_min = salary_max = int(value)
            
            # Extract employment type
            employment_type = schema_data.get('employmentType', 'full_time')
            if isinstance(employment_type, list):
                employment_type = employment_type[0] if employment_type else 'full_time'
            
            # Map employment type to our format
            job_type_mapping = {
                'FULL_TIME': 'full_time',
                'PART_TIME': 'part_time',
                'CONTRACT': 'contract',
                'CONTRACTOR': 'contract',
                'TEMPORARY': 'contract',
                'INTERN': 'internship',
                'INTERNSHIP': 'internship',
                'VOLUNTEER': 'part_time',
                'OTHER': 'full_time'
            }
            
            job_type = job_type_mapping.get(employment_type.upper(), 'full_time')
            
            # Extract dates
            posted_date = schema_data.get('datePosted')
            if posted_date:
                try:
                    posted_date = datetime.fromisoformat(posted_date.replace('Z', '+00:00'))
                except:
                    posted_date = datetime.utcnow()
            else:
                posted_date = datetime.utcnow()
            
            # Extract application info
            application_url = url  # Default to the job page URL
            application_email = None
            
            # Look for application URLs
            if 'applicationContact' in schema_data:
                contact = schema_data['applicationContact']
                if isinstance(contact, dict):
                    application_email = contact.get('email')
            
            # Generate external ID from URL
            external_id = f"schema_{hash(url)}"
            
            # Create job data
            job_data = JobData(
                title=title.strip(),
                company=company.strip(),
                location=location.strip(),
                description=description.strip(),
                requirements="See job posting for requirements",
                benefits="See job posting for benefits",
                salary_min=salary_min,
                salary_max=salary_max,
                job_type=job_type,
                application_url=application_url,
                application_email=application_email,
                external_id=external_id,
                external_url=url,
                posted_date=posted_date,
                source="schema"
            )
            
            return job_data
            
        except Exception as e:
            print(f"Error parsing job schema: {e}")
            return None
    
    def _extract_job_from_html(self, soup: BeautifulSoup, url: str) -> Optional[JobData]:
        """Fallback HTML extraction if no schema found."""
        
        try:
            # Try to extract basic information from HTML
            title = ""
            company = ""
            description = ""
            
            # Look for common title patterns
            title_selectors = ['h1', '.job-title', '.position-title', '[class*="title"]']
            for selector in title_selectors:
                element = soup.select_one(selector)
                if element:
                    title = element.get_text().strip()
                    break
            
            # Look for company information
            company_selectors = ['.company-name', '[class*="company"]', '[class*="organization"]']
            for selector in company_selectors:
                element = soup.select_one(selector)
                if element:
                    company = element.get_text().strip()
                    break
            
            # Get description from the main content
            description_selectors = ['.job-description', '.description', '.content', 'main']
            for selector in description_selectors:
                element = soup.select_one(selector)
                if element:
                    description = element.get_text().strip()[:1000]  # Limit to 1000 chars
                    break
            
            if title and company:
                return JobData(
                    title=title,
                    company=company,
                    location="Location not specified",
                    description=description,
                    requirements="See job posting for requirements",
                    benefits="See job posting for benefits",
                    salary_min=None,
                    salary_max=None,
                    job_type="full_time",
                    application_url=url,
                    application_email=None,
                    external_id=f"html_{hash(url)}",
                    external_url=url,
                    posted_date=datetime.utcnow(),
                    source="schema_html"
                )
            
        except Exception as e:
            print(f"Error extracting from HTML: {e}")
        
        return None
    
    def _matches_criteria(self, job_data: JobData, keywords: List[str], locations: List[str]) -> bool:
        """Check if job matches search criteria."""
        
        # Check keywords
        text_to_search = f"{job_data.title} {job_data.description} {job_data.company}".lower()
        keyword_match = any(keyword.lower() in text_to_search for keyword in keywords)
        
        # Check locations (if specified)
        if locations:
            location_match = any(location.lower() in job_data.location.lower() for location in locations)
        else:
            location_match = True
        
        return keyword_match and location_match
    
    async def get_job_details(self, job_url: str) -> Optional[JobData]:
        """Get detailed job information from a URL."""
        async with httpx.AsyncClient(headers=self.headers, timeout=30) as client:
            return await self._extract_job_from_page(client, job_url) 