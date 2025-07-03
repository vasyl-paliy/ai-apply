#!/usr/bin/env python3
"""Test script to debug MockScraper functionality."""

import asyncio
import sys
import os

# Add the backend directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from scrapers.mock_scraper import MockScraper


async def test_mock_scraper():
    """Test the MockScraper directly."""
    print("Testing MockScraper...")
    
    try:
        async with MockScraper() as scraper:
            print("MockScraper initialized successfully")
            
            # Test search_jobs method
            jobs = await scraper.search_jobs(
                keywords=["software engineer"],
                locations=["Remote"],
                max_results=10
            )
            
            print(f"Found {len(jobs)} jobs")
            
            for i, job in enumerate(jobs[:3]):  # Show first 3 jobs
                print(f"\nJob {i+1}:")
                print(f"  Title: {job.title}")
                print(f"  Company: {job.company}")
                print(f"  Location: {job.location}")
                print(f"  Source: {job.source}")
                print(f"  External ID: {job.external_id}")
                print(f"  Salary: ${job.salary_min:,} - ${job.salary_max:,}")
                
        print("\nTest completed successfully!")
        
    except Exception as e:
        print(f"Error testing MockScraper: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_mock_scraper()) 