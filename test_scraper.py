#!/usr/bin/env python3
"""Test script for MockScraper to debug the scraping issue."""

import asyncio
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from backend.scrapers.mock_scraper import MockScraper

async def test_mock_scraper():
    """Test the MockScraper directly."""
    print("Testing MockScraper...")
    
    try:
        async with MockScraper() as scraper:
            print("MockScraper initialized successfully")
            
            jobs = await scraper.search_jobs(
                keywords=["software engineer"],
                locations=["Remote"],
                max_results=5
            )
            
            print(f"Found {len(jobs)} jobs:")
            for i, job in enumerate(jobs, 1):
                print(f"{i}. {job.title} at {job.company} - {job.location}")
                
        print("Test completed successfully!")
        return True
        
    except Exception as e:
        print(f"Error during test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_mock_scraper())
    sys.exit(0 if success else 1) 