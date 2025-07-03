"""
API-based job scraper using legitimate job APIs.
These are much more reliable and respectful than scraping.
"""

import asyncio
import httpx
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from .base_scraper import BaseScraper, JobData
import os


class APIJobScraper(BaseScraper):
    """Job scraper using legitimate APIs."""
    
    def __init__(self):
        super().__init__()
        self.apis = {
            'jsearch': {
                'url': 'https://jsearch.p.rapidapi.com/search',
                'headers': {
                    'X-RapidAPI-Key': os.getenv('RAPIDAPI_KEY', ''),
                    'X-RapidAPI-Host': 'jsearch.p.rapidapi.com'
                }
            },
            'indeed': {
                'url': 'https://api.indeed.com/ads/apisearch',
                'publisher_id': os.getenv('INDEED_PUBLISHER_ID', ''),
                'format': 'json',
                'v': '2'
            },
            'reed': {
                'url': 'https://www.reed.co.uk/api/1.0/search',
                'headers': {
                    'Authorization': f"Basic {os.getenv('REED_API_KEY', '')}"
                }
            }
        }
    
    async def login(self):
        """APIs don't require login, just API keys."""
        print("API-based scraper initialized")
        return True
    
    async def search_jobs(
        self,
        keywords: List[str],
        locations: List[str],
        job_types: Optional[List[str]] = None,
        salary_min: Optional[int] = None,
        max_results: int = 50
    ) -> List[JobData]:
        """Search jobs using multiple APIs."""
        
        all_jobs = []
        
        # Try JSearch API (RapidAPI)
        if self.apis['jsearch']['headers']['X-RapidAPI-Key']:
            jsearch_jobs = await self._search_jsearch(keywords, locations, max_results)
            all_jobs.extend(jsearch_jobs)
        
        # Try Indeed API (if publisher ID available)
        if self.apis['indeed']['publisher_id']:
            indeed_jobs = await self._search_indeed_api(keywords, locations, max_results)
            all_jobs.extend(indeed_jobs)
        
        # Try Reed API (UK focused)
        if self.apis['reed']['headers']['Authorization']:
            reed_jobs = await self._search_reed(keywords, locations, max_results)
            all_jobs.extend(reed_jobs)
        
        # Remove duplicates based on external_id
        unique_jobs = []
        seen_ids = set()
        
        for job in all_jobs:
            if job.external_id not in seen_ids:
                unique_jobs.append(job)
                seen_ids.add(job.external_id)
        
        print(f"API scraper found {len(unique_jobs)} unique jobs from {len(all_jobs)} total")
        return unique_jobs[:max_results]
    
    async def _search_jsearch(self, keywords: List[str], locations: List[str], max_results: int) -> List[JobData]:
        """Search using JSearch API (RapidAPI)."""
        jobs = []
        
        try:
            async with httpx.AsyncClient() as client:
                for keyword in keywords:
                    for location in locations:
                        params = {
                            'query': keyword,
                            'page': '1',
                            'num_pages': '1',
                            'location': location,
                            'remote_jobs_only': 'true' if 'remote' in location.lower() else 'false'
                        }
                        
                        response = await client.get(
                            self.apis['jsearch']['url'],
                            params=params,
                            headers=self.apis['jsearch']['headers'],
                            timeout=30
                        )
                        
                        if response.status_code == 200:
                            data = response.json()
                            for job_data in data.get('data', []):
                                job = self._convert_jsearch_job(job_data)
                                if job:
                                    jobs.append(job)
                        else:
                            print(f"JSearch API error: {response.status_code}")
                        
                        # Rate limiting
                        await asyncio.sleep(1)
                        
        except Exception as e:
            print(f"JSearch API search failed: {e}")
        
        return jobs
    
    async def _search_indeed_api(self, keywords: List[str], locations: List[str], max_results: int) -> List[JobData]:
        """Search using Indeed Publisher API."""
        jobs = []
        
        try:
            async with httpx.AsyncClient() as client:
                for keyword in keywords:
                    for location in locations:
                        params = {
                            'publisher': self.apis['indeed']['publisher_id'],
                            'q': keyword,
                            'l': location,
                            'sort': 'date',
                            'radius': '25',
                            'st': 'jobsite',
                            'jt': 'fulltime',
                            'start': '0',
                            'limit': str(min(25, max_results)),
                            'fromage': '14',
                            'format': 'json',
                            'v': '2'
                        }
                        
                        response = await client.get(
                            self.apis['indeed']['url'],
                            params=params,
                            timeout=30
                        )
                        
                        if response.status_code == 200:
                            data = response.json()
                            for job_data in data.get('results', []):
                                job = self._convert_indeed_job(job_data)
                                if job:
                                    jobs.append(job)
                        
                        await asyncio.sleep(1)
                        
        except Exception as e:
            print(f"Indeed API search failed: {e}")
        
        return jobs
    
    async def _search_reed(self, keywords: List[str], locations: List[str], max_results: int) -> List[JobData]:
        """Search using Reed API (UK focused)."""
        jobs = []
        
        try:
            async with httpx.AsyncClient() as client:
                for keyword in keywords:
                    for location in locations:
                        params = {
                            'keywords': keyword,
                            'location': location,
                            'resultsToTake': min(100, max_results),
                            'resultsToSkip': 0
                        }
                        
                        response = await client.get(
                            self.apis['reed']['url'],
                            params=params,
                            headers=self.apis['reed']['headers'],
                            timeout=30
                        )
                        
                        if response.status_code == 200:
                            data = response.json()
                            for job_data in data.get('results', []):
                                job = self._convert_reed_job(job_data)
                                if job:
                                    jobs.append(job)
                        
                        await asyncio.sleep(1)
                        
        except Exception as e:
            print(f"Reed API search failed: {e}")
        
        return jobs
    
    def _convert_jsearch_job(self, job_data: Dict[str, Any]) -> Optional[JobData]:
        """Convert JSearch API response to JobData."""
        try:
            return JobData(
                title=job_data.get('job_title', ''),
                company=job_data.get('employer_name', ''),
                location=job_data.get('job_city', '') + ', ' + job_data.get('job_state', ''),
                description=job_data.get('job_description', ''),
                requirements=job_data.get('job_highlights', {}).get('Qualifications', [''])[0],
                benefits=job_data.get('job_highlights', {}).get('Benefits', [''])[0],
                salary_min=job_data.get('job_min_salary'),
                salary_max=job_data.get('job_max_salary'),
                job_type=job_data.get('job_employment_type', 'full_time').lower(),
                application_url=job_data.get('job_apply_link', ''),
                application_email=None,
                external_id=job_data.get('job_id', ''),
                external_url=job_data.get('job_apply_link', ''),
                posted_date=datetime.now() - timedelta(days=1),
                source='jsearch'
            )
        except Exception as e:
            print(f"Error converting JSearch job: {e}")
            return None
    
    def _convert_indeed_job(self, job_data: Dict[str, Any]) -> Optional[JobData]:
        """Convert Indeed API response to JobData."""
        try:
            return JobData(
                title=job_data.get('jobtitle', ''),
                company=job_data.get('company', ''),
                location=job_data.get('formattedLocationFull', ''),
                description=job_data.get('snippet', ''),
                requirements='See job posting for requirements',
                benefits='See job posting for benefits',
                salary_min=None,
                salary_max=None,
                job_type='full_time',
                application_url=job_data.get('url', ''),
                application_email=None,
                external_id=job_data.get('jobkey', ''),
                external_url=job_data.get('url', ''),
                posted_date=datetime.now() - timedelta(days=1),
                source='indeed_api'
            )
        except Exception as e:
            print(f"Error converting Indeed job: {e}")
            return None
    
    def _convert_reed_job(self, job_data: Dict[str, Any]) -> Optional[JobData]:
        """Convert Reed API response to JobData."""
        try:
            return JobData(
                title=job_data.get('jobTitle', ''),
                company=job_data.get('employerName', ''),
                location=job_data.get('locationName', ''),
                description=job_data.get('jobDescription', ''),
                requirements='See job posting for requirements',
                benefits='See job posting for benefits',
                salary_min=job_data.get('minimumSalary'),
                salary_max=job_data.get('maximumSalary'),
                job_type='full_time',
                application_url=job_data.get('jobUrl', ''),
                application_email=None,
                external_id=str(job_data.get('jobId', '')),
                external_url=job_data.get('jobUrl', ''),
                posted_date=datetime.now() - timedelta(days=1),
                source='reed'
            )
        except Exception as e:
            print(f"Error converting Reed job: {e}")
            return None
    
    async def get_job_details(self, job_url: str) -> Optional[JobData]:
        """Get detailed job information - not needed for APIs."""
        return None 