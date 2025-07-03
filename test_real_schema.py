#!/usr/bin/env python3
"""
Enhanced test for Google Jobs Schema scraper.
This test looks at individual job pages and job boards more likely to have schema.
"""

import asyncio
import json
import httpx
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import re


class EnhancedSchemaTest:
    """Enhanced test class for JobPosting schema discovery."""
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
        }
        
        # Test organizations more likely to have schema
        self.test_organizations = [
            # Job boards that often use schema
            'https://www.glassdoor.com/Jobs/index.htm',
            'https://www.indeed.com/jobs',
            'https://www.ziprecruiter.com/jobs',
            'https://www.monster.com/jobs',
            'https://stackoverflow.com/jobs',
            
            # Smaller organizations and startups
            'https://jobs.lever.co',
            'https://boards.greenhouse.io',
            
            # ATS platforms that often implement schema
            'https://apply.workable.com',
            'https://jobs.smartrecruiters.com',
            
            # Academic institutions (more likely to use schema)
            'https://careers.harvard.edu',
            'https://careers.mit.edu',
            'https://jobs.yale.edu',
        ]
        
        # Specific job posting URLs to test
        self.test_job_urls = [
            # These are examples - we'll discover real ones
            'https://jobs.lever.co/example',
            'https://boards.greenhouse.io/example',
        ]
    
    async def run_comprehensive_test(self):
        """Run a comprehensive test for JobPosting schema."""
        
        print("🚀 ENHANCED GOOGLE JOBS SCHEMA TEST")
        print("=" * 70)
        print("This test will:")
        print("1. Check main career pages for schema")
        print("2. Look for individual job posting links")
        print("3. Test specific job pages for JobPosting data")
        print("4. Check job boards and ATS platforms")
        print()
        
        all_found_jobs = []
        
        timeout = httpx.Timeout(20.0, connect=8.0)
        
        async with httpx.AsyncClient(
            headers=self.headers, 
            timeout=timeout,
            follow_redirects=True
        ) as client:
            
            # Phase 1: Check main pages and discover job links
            print("🔍 PHASE 1: Discovering job posting pages")
            print("-" * 50)
            
            discovered_job_pages = []
            
            for i, org_url in enumerate(self.test_organizations, 1):
                print(f"[{i}/{len(self.test_organizations)}] Checking {org_url}")
                
                try:
                    # Check main page for schema
                    main_page_jobs = await self._check_page_for_jobs(client, org_url)
                    if main_page_jobs:
                        print(f"  ✅ Found {len(main_page_jobs)} jobs on main page!")
                        all_found_jobs.extend(main_page_jobs)
                    
                    # Look for individual job links
                    job_links = await self._find_job_links(client, org_url)
                    if job_links:
                        print(f"  📄 Discovered {len(job_links)} job posting links")
                        discovered_job_pages.extend(job_links[:3])  # Test first 3
                    else:
                        print(f"  ❌ No job links found")
                    
                    await asyncio.sleep(1)
                    
                except Exception as e:
                    print(f"  ❌ Error: {str(e)[:50]}...")
                
                print()
            
            # Phase 2: Test individual job pages
            if discovered_job_pages:
                print("🎯 PHASE 2: Testing individual job pages")
                print("-" * 50)
                
                for i, job_url in enumerate(discovered_job_pages[:10], 1):  # Test first 10
                    print(f"[{i}/10] Testing job page: {job_url}")
                    
                    try:
                        job_page_jobs = await self._check_page_for_jobs(client, job_url)
                        if job_page_jobs:
                            print(f"  ✅ Found JobPosting schema!")
                            all_found_jobs.extend(job_page_jobs)
                            
                            # Show the job details
                            job = job_page_jobs[0]
                            print(f"     📝 {job.get('title', 'No title')}")
                            print(f"     🏢 {job.get('company', 'Unknown company')}")
                            print(f"     📍 {job.get('location', 'No location')}")
                        else:
                            print(f"  ❌ No schema found")
                        
                        await asyncio.sleep(1)
                        
                    except Exception as e:
                        print(f"  ❌ Error: {str(e)[:50]}...")
                    
                    print()
        
        # Final Results
        print("📊 FINAL RESULTS")
        print("=" * 70)
        print(f"Total JobPosting schemas found: {len(all_found_jobs)}")
        
        if all_found_jobs:
            print("✅ SUCCESS! JobPosting schema data is available!")
            print()
            print("Real jobs found with schema:")
            
            for i, job in enumerate(all_found_jobs[:10], 1):
                print(f"{i}. {job.get('title', 'No title')}")
                print(f"   Company: {job.get('company', 'Unknown')}")
                print(f"   Location: {job.get('location', 'No location')}")
                print(f"   URL: {job.get('url', 'No URL')}")
                if job.get('salary'):
                    print(f"   Salary: {job['salary']}")
                print()
            
            print("🎉 The Google Jobs Schema scraper approach WORKS!")
            print("We found real JobPosting structured data that can be extracted!")
            
        else:
            print("❌ No JobPosting schemas found")
            print()
            print("Possible reasons:")
            print("- Many organizations use dynamic loading (JavaScript)")
            print("- Schema may be implemented differently than expected")
            print("- Some sites may require authentication")
            print("- Rate limiting or blocking may be occurring")
            print()
            print("💡 Recommendations:")
            print("- Try using a browser automation tool (Playwright)")
            print("- Look at smaller organizations and job boards")
            print("- Check specific ATS platforms (Greenhouse, Lever)")
            print("- Test with different user agents or timing")
    
    async def _find_job_links(self, client: httpx.AsyncClient, base_url: str) -> list:
        """Find individual job posting links from a career page."""
        
        job_links = []
        
        try:
            response = await client.get(base_url)
            if response.status_code != 200:
                return job_links
            
            soup = BeautifulSoup(response.text, 'html.parser')
            base_domain = urlparse(base_url).netloc
            
            # Look for job-related links
            for link in soup.find_all('a', href=True):
                href = link['href']
                link_text = link.get_text().lower()
                
                # Check if this looks like a job posting link
                job_indicators = ['job', 'position', 'opening', 'role', 'career', 'apply']
                
                if (any(indicator in href.lower() for indicator in job_indicators) or
                    any(indicator in link_text for indicator in ['view job', 'apply', 'details'])):
                    
                    full_url = urljoin(base_url, href)
                    
                    # Only include links from the same domain
                    if urlparse(full_url).netloc == base_domain:
                        job_links.append(full_url)
            
        except Exception as e:
            pass
        
        return list(set(job_links))  # Remove duplicates
    
    async def _check_page_for_jobs(self, client: httpx.AsyncClient, url: str) -> list:
        """Check a single page for JobPosting schema data."""
        
        jobs = []
        
        try:
            response = await client.get(url)
            if response.status_code != 200:
                return jobs
            
            # First, let's see if there's any mention of structured data
            content = response.text.lower()
            has_json_ld = 'application/ld+json' in content
            has_jobposting = 'jobposting' in content
            
            if not has_json_ld and not has_jobposting:
                return jobs  # No point parsing if no structured data
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
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
            
            return {
                'title': title,
                'company': company,
                'location': location,
                'description': description[:200] + '...' if len(description) > 200 else description,
                'salary': salary_info,
                'posted_date': posted_date,
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
    """Run the enhanced schema discovery test."""
    
    tester = EnhancedSchemaTest()
    await tester.run_comprehensive_test()


if __name__ == "__main__":
    asyncio.run(main()) 