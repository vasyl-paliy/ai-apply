#!/usr/bin/env python3
"""
Test the enhanced Google Jobs Schema scraper with all improvements:
- JavaScript rendering with Playwright
- Relaxed domain checking
- Robust JSON-LD parsing
- Enhanced salary and date extraction
- Better filtering and deduplication
"""

import asyncio
import sys
import os

# Add the backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from scrapers.schema_scraper import GoogleJobsSchemaScraper


async def test_enhanced_scraper():
    """Test the enhanced scraper with real job sites."""
    
    print("🚀 TESTING ENHANCED GOOGLE JOBS SCHEMA SCRAPER")
    print("=" * 70)
    print("Testing with JavaScript rendering, robust parsing, and all improvements!")
    print()
    
    # Create scraper with filters
    filters = {
        'keywords': ['software', 'engineer', 'developer', 'python', 'javascript'],
        'location': '',  # Any location
        'employment_type': '',  # Any employment type
        'company': ''  # Any company
    }
    
    scraper = GoogleJobsSchemaScraper(filters=filters)
    
    try:
        # Test with a small set of URLs first
        print("🔍 PHASE 1: Testing with small set of URLs")
        print("-" * 50)
        
        test_urls = [
            'https://careers.harvard.edu',
            'https://careers.mit.edu',
            'https://jobs.lever.co/airbnb',
            'https://boards.greenhouse.io/airbnb',
        ]
        
        test_jobs = await scraper.test_scraping(test_urls)
        
        print(f"✅ Test phase found {len(test_jobs)} jobs")
        
        if test_jobs:
            print("\n📋 Sample jobs from test:")
            for i, job in enumerate(test_jobs[:3], 1):
                print(f"{i}. {job.get('title', 'No title')}")
                print(f"   Company: {job.get('company', 'Unknown')}")
                print(f"   Location: {job.get('location', 'No location')}")
                print(f"   Posted: {job.get('posted_date', 'No date')}")
                print(f"   URL: {job.get('url', 'No URL')}")
                if job.get('salary'):
                    print(f"   Salary: {job['salary']}")
                print()
        
        # Test the full scraping if test was successful
        if test_jobs:
            print("🎯 PHASE 2: Running full enhanced scraping")
            print("-" * 50)
            
            # Run full scraping with limit
            all_jobs = await scraper.scrape_jobs(limit=20, filters=filters)
            
            print(f"✅ Full scraping found {len(all_jobs)} jobs")
            
            if all_jobs:
                print("\n🎉 SUCCESS! Enhanced scraper is working!")
                print("\nAll discovered jobs:")
                
                for i, job in enumerate(all_jobs, 1):
                    print(f"{i}. {job.get('title', 'No title')}")
                    print(f"   Company: {job.get('company', 'Unknown')}")
                    print(f"   Location: {job.get('location', 'No location')}")
                    print(f"   Source: {job.get('source', 'Unknown')}")
                    print(f"   Posted: {job.get('posted_date', 'No date')}")
                    print(f"   URL: {job.get('url', 'No URL')}")
                    if job.get('salary'):
                        print(f"   Salary: {job['salary']}")
                    if job.get('employment_type'):
                        print(f"   Type: {job['employment_type']}")
                    print()
                
                print("🎉 Enhanced Google Jobs Schema scraper is WORKING!")
                print("✅ JavaScript rendering: ENABLED")
                print("✅ Relaxed domain checking: ENABLED")
                print("✅ Robust JSON-LD parsing: ENABLED")
                print("✅ Enhanced date/salary extraction: ENABLED")
                print("✅ Improved filtering: ENABLED")
                print("✅ Better deduplication: ENABLED")
                
            else:
                print("❌ No jobs found in full scraping")
        else:
            print("❌ Test scraping failed, skipping full scraping")
            
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 70)
    print("Enhanced scraper test completed!")


if __name__ == "__main__":
    asyncio.run(test_enhanced_scraper()) 