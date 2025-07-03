#!/usr/bin/env python3
"""
Smart test for JobPosting schema that handles search interfaces.
This test can perform searches and navigate to actual job listings.
"""

import asyncio
import json
import httpx
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, urlencode
import re


class SmartJobSchemaTest:
    """Smart test that handles search interfaces and finds real job postings."""
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
        }
        
        # Organizations with search interfaces
        self.search_configs = [
            {
                'name': 'MIT Careers',
                'base_url': 'https://careers.mit.edu',
                'search_paths': [
                    '/search?q=software',
                    '/search?q=engineer',
                    '/search?q=developer',
                    '/jobs/search?keyword=software',
                    '/jobs'
                ]
            },
            {
                'name': 'Harvard Careers',
                'base_url': 'https://careers.harvard.edu',
                'search_paths': [
                    '/search?q=software',
                    '/search?q=engineer',
                    '/jobs/search?keyword=software',
                    '/jobs'
                ]
            },
            {
                'name': 'Stanford Careers',
                'base_url': 'https://careers.stanford.edu',
                'search_paths': [
                    '/go/search?q=software',
                    '/go/search?q=engineer',
                    '/jobs'
                ]
            },
            {
                'name': 'Monster Jobs',
                'base_url': 'https://www.monster.com',
                'search_paths': [
                    '/jobs/search?q=software%20engineer',
                    '/jobs/search?q=developer',
                    '/jobs/search?q=python',
                    '/jobs/l-remote'
                ]
            },
            {
                'name': 'Greenhouse Boards',
                'base_url': 'https://boards.greenhouse.io',
                'search_paths': [
                    '/embed/job_board?for=airbnb',
                    '/embed/job_board?for=stripe',
                    '/embed/job_board?for=notion',
                    '/embed/job_board?for=github'
                ]
            },
            {
                'name': 'Lever Jobs',
                'base_url': 'https://jobs.lever.co',
                'search_paths': [
                    '/airbnb',
                    '/stripe',
                    '/notion',
                    '/github'
                ]
            }
        ]
        
        # Common job search terms
        self.search_terms = ['software', 'engineer', 'developer', 'python', 'remote']
    
    async def run_smart_test(self):
        """Run smart test that handles search interfaces."""
        
        print("🧠 SMART GOOGLE JOBS SCHEMA TEST")
        print("=" * 70)
        print("This test will:")
        print("1. Navigate to career sites with search interfaces")
        print("2. Perform searches to find actual job listings")
        print("3. Extract real job posting URLs")
        print("4. Test job pages for JobPosting schema")
        print()
        
        all_found_jobs = []
        
        timeout = httpx.Timeout(30.0, connect=10.0)
        
        async with httpx.AsyncClient(
            headers=self.headers, 
            timeout=timeout,
            follow_redirects=True
        ) as client:
            
            for i, config in enumerate(self.search_configs, 1):
                print(f"🔍 [{i}/{len(self.search_configs)}] Testing {config['name']}")
                print("-" * 50)
                
                try:
                    # Test different search paths
                    for search_path in config['search_paths']:
                        search_url = config['base_url'] + search_path
                        print(f"  Searching: {search_url}")
                        
                        # Check if this search URL has job listings
                        search_jobs = await self._check_search_results(client, search_url)
                        
                        if search_jobs:
                            print(f"  ✅ Found {len(search_jobs)} job links from search!")
                            
                            # Test first few job links for schema
                            for j, job_url in enumerate(search_jobs[:3], 1):
                                print(f"    [{j}] Testing job: {job_url}")
                                
                                try:
                                    job_schema = await self._check_page_for_jobs(client, job_url)
                                    if job_schema:
                                        print(f"      ✅ Found JobPosting schema!")
                                        all_found_jobs.extend(job_schema)
                                        
                                        # Show job details
                                        job = job_schema[0]
                                        print(f"         📝 {job.get('title', 'No title')}")
                                        print(f"         🏢 {job.get('company', 'Unknown')}")
                                        print(f"         📍 {job.get('location', 'No location')}")
                                    else:
                                        print(f"      ❌ No schema found")
                                    
                                    await asyncio.sleep(0.5)
                                    
                                except Exception as e:
                                    print(f"      ❌ Error: {str(e)[:40]}...")
                            
                            break  # Found jobs, no need to try other search paths
                        else:
                            print(f"  ❌ No job links found")
                        
                        await asyncio.sleep(1)
                    
                except Exception as e:
                    print(f"  ❌ Error with {config['name']}: {str(e)[:50]}...")
                
                print()
        
        # Results
        print("📊 SMART TEST RESULTS")
        print("=" * 70)
        print(f"Total JobPosting schemas found: {len(all_found_jobs)}")
        
        if all_found_jobs:
            print("🎉 SUCCESS! Found real JobPosting schema data!")
            print()
            print("Real jobs with schema:")
            
            for i, job in enumerate(all_found_jobs, 1):
                print(f"{i}. {job.get('title', 'No title')}")
                print(f"   Company: {job.get('company', 'Unknown')}")
                print(f"   Location: {job.get('location', 'No location')}")
                print(f"   Posted: {job.get('posted_date', 'No date')}")
                print(f"   URL: {job.get('url', 'No URL')}")
                if job.get('salary'):
                    print(f"   Salary: {job['salary']}")
                if job.get('description'):
                    print(f"   Description: {job['description'][:100]}...")
                print()
            
            print("✅ The Google Jobs Schema scraper approach IS WORKING!")
            print("We successfully found real job postings with structured data!")
            
        else:
            print("❌ No JobPosting schemas found yet")
            print()
            print("This suggests we need to:")
            print("- Use browser automation (Playwright/Selenium)")
            print("- Handle JavaScript-rendered content")
            print("- Try more specific job board URLs")
            print("- Test with authentication if needed")
    
    async def _check_search_results(self, client: httpx.AsyncClient, search_url: str) -> list:
        """Check search results page for job listing URLs."""
        
        job_urls = []
        
        try:
            response = await client.get(search_url)
            if response.status_code != 200:
                return job_urls
            
            soup = BeautifulSoup(response.text, 'html.parser')
            base_domain = urlparse(search_url).netloc
            
            # Look for job listing links using various patterns
            job_patterns = [
                # Generic job patterns
                r'/job[s]?/[0-9]+',
                r'/job[s]?/[a-zA-Z0-9\-]+',
                r'/position[s]?/[a-zA-Z0-9\-]+',
                r'/career[s]?/[a-zA-Z0-9\-]+',
                r'/opening[s]?/[a-zA-Z0-9\-]+',
                
                # Specific platform patterns
                r'/jobs/view/[0-9]+',
                r'/jobs/detail/[a-zA-Z0-9\-]+',
                r'/apply/[a-zA-Z0-9\-]+',
                r'/postings/[a-zA-Z0-9\-]+',
            ]
            
            # Check all links
            for link in soup.find_all('a', href=True):
                href = link['href']
                
                # Check if this matches job patterns
                for pattern in job_patterns:
                    if re.search(pattern, href, re.IGNORECASE):
                        full_url = urljoin(search_url, href)
                        
                        # Only include links from the same domain
                        if urlparse(full_url).netloc == base_domain:
                            job_urls.append(full_url)
                        break
                
                # Also check link text for job indicators
                link_text = link.get_text().lower()
                if any(indicator in link_text for indicator in ['view job', 'apply now', 'job details', 'position']):
                    full_url = urljoin(search_url, href)
                    if urlparse(full_url).netloc == base_domain:
                        job_urls.append(full_url)
            
            # Remove duplicates and limit results
            job_urls = list(set(job_urls))[:10]
            
        except Exception as e:
            pass
        
        return job_urls
    
    async def _check_page_for_jobs(self, client: httpx.AsyncClient, url: str) -> list:
        """Check a page for JobPosting schema data."""
        
        jobs = []
        
        try:
            response = await client.get(url)
            if response.status_code != 200:
                return jobs
            
            content = response.text
            
            # Quick check for structured data
            if 'application/ld+json' not in content.lower():
                return jobs
            
            soup = BeautifulSoup(content, 'html.parser')
            
            # Look for JSON-LD script tags
            script_tags = soup.find_all('script', type='application/ld+json')
            
            for script in script_tags:
                if not script.string:
                    continue
                
                try:
                    data = json.loads(script.string)
                    
                    # Handle both single objects and arrays
                    if isinstance(data, list):
                        for item in data:
                            if self._is_job_posting(item):
                                job = self._extract_job_data(item, url)
                                if job:
                                    jobs.append(job)
                    else:
                        if self._is_job_posting(data):
                            job = self._extract_job_data(data, url)
                            if job:
                                jobs.append(job)
                
                except json.JSONDecodeError:
                    continue
        
        except Exception as e:
            pass
        
        return jobs
    
    def _is_job_posting(self, data):
        """Check if data represents a JobPosting."""
        if isinstance(data, dict):
            return data.get('@type') == 'JobPosting'
        return False
    
    def _extract_job_data(self, data, source_url):
        """Extract key data from JobPosting schema."""
        
        try:
            # Extract basic info
            title = data.get('title', '')
            description = data.get('description', '')
            
            # Extract company
            hiring_org = data.get('hiringOrganization', {})
            if isinstance(hiring_org, dict):
                company = hiring_org.get('name', '')
            else:
                company = str(hiring_org)
            
            # Extract location
            job_location = data.get('jobLocation', {})
            location = self._extract_location(job_location)
            
            # Extract salary
            salary_info = self._extract_salary(data.get('baseSalary', {}))
            
            # Extract dates
            posted_date = data.get('datePosted', '')
            
            # Extract URL
            job_url = data.get('url', source_url)
            
            # Extract employment type
            employment_type = data.get('employmentType', '')
            
            return {
                'title': title,
                'company': company,
                'location': location,
                'description': description[:150] + '...' if len(description) > 150 else description,
                'salary': salary_info,
                'posted_date': posted_date,
                'employment_type': employment_type,
                'url': job_url,
                'source_url': source_url
            }
            
        except Exception as e:
            return None
    
    def _extract_location(self, job_location):
        """Extract location from JobPosting location data."""
        
        if not isinstance(job_location, dict):
            return str(job_location) if job_location else "Location not specified"
        
        address = job_location.get('address', {})
        if isinstance(address, dict):
            city = address.get('addressLocality', '')
            state = address.get('addressRegion', '')
            country = address.get('addressCountry', '')
            
            location_parts = [part for part in [city, state, country] if part]
            return ', '.join(location_parts) if location_parts else "Location not specified"
        
        return str(address) if address else "Location not specified"
    
    def _extract_salary(self, salary_data):
        """Extract salary information."""
        
        if not isinstance(salary_data, dict):
            return None
        
        try:
            value = salary_data.get('value', {})
            
            if isinstance(value, dict):
                min_val = value.get('minValue')
                max_val = value.get('maxValue')
                single_val = value.get('value')
                
                if min_val and max_val:
                    return f"${min_val:,} - ${max_val:,}"
                elif single_val:
                    return f"${single_val:,}"
            
            elif isinstance(value, (int, float)):
                return f"${int(value):,}"
        
        except:
            pass
        
        return None


async def main():
    """Run the smart schema test."""
    
    tester = SmartJobSchemaTest()
    await tester.run_smart_test()


if __name__ == "__main__":
    asyncio.run(main()) 