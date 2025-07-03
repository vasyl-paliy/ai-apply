"""Command-line interface for AutoApply AI."""

import asyncio
import click
from typing import List

from .config import settings
from ..scrapers.linkedin_scraper import LinkedInScraper
from ..generators.cover_letter_generator import CoverLetterGenerator, CoverLetterRequest


@click.group()
def cli():
    """AutoApply AI Command Line Interface."""
    pass


@cli.command()
@click.option('--keywords', '-k', multiple=True, required=True, help='Job search keywords')
@click.option('--locations', '-l', multiple=True, help='Job locations')
@click.option('--max-results', default=10, help='Maximum number of results')
async def search_jobs(keywords: List[str], locations: List[str], max_results: int):
    """Search for jobs using LinkedIn scraper."""
    click.echo(f"🔍 Searching for jobs with keywords: {', '.join(keywords)}")
    click.echo(f"📍 Locations: {', '.join(locations) if locations else 'Any'}")
    click.echo(f"📊 Max results: {max_results}")
    click.echo("=" * 50)
    
    try:
        async with LinkedInScraper() as scraper:
            jobs = await scraper.scrape_jobs(
                keywords=list(keywords),
                locations=list(locations),
                max_results=max_results
            )
            
            if jobs:
                click.echo(f"✅ Found {len(jobs)} jobs:")
                for i, job in enumerate(jobs, 1):
                    click.echo(f"\n{i}. {job.title}")
                    click.echo(f"   Company: {job.company}")
                    click.echo(f"   Location: {job.location}")
                    click.echo(f"   URL: {job.external_url}")
                    if job.salary_min and job.salary_max:
                        click.echo(f"   Salary: ${job.salary_min:,} - ${job.salary_max:,}")
            else:
                click.echo("❌ No jobs found")
                
    except Exception as e:
        click.echo(f"❌ Error searching jobs: {e}")


@cli.command()
@click.option('--job-title', required=True, help='Job title')
@click.option('--company', required=True, help='Company name')
@click.option('--job-description', required=True, help='Job description')
@click.option('--name', default='John Doe', help='Your name')
@click.option('--tone', default='professional', help='Cover letter tone')
@click.option('--length', default='medium', help='Cover letter length')
def generate_cover_letter(job_title: str, company: str, job_description: str, 
                         name: str, tone: str, length: str):
    """Generate a sample cover letter."""
    click.echo(f"✍️  Generating cover letter for {company} - {job_title}")
    click.echo(f"👤 Candidate: {name}")
    click.echo(f"🎭 Tone: {tone}")
    click.echo(f"📏 Length: {length}")
    click.echo("=" * 50)
    
    # Create mock job data
    from ..scrapers.base_scraper import JobData
    job_data = JobData(
        title=job_title,
        company=company,
        location="Remote",
        description=job_description,
        requirements="",
        benefits="",
        salary_min=None,
        salary_max=None,
        job_type="full_time",
        application_url="https://example.com",
        application_email=None,
        external_id="test-123",
        external_url="https://example.com",
        posted_date=None,
        source="test"
    )
    
    # Create mock user profile
    user_profile = {
        'full_name': name,
        'skills': ['Python', 'FastAPI', 'PostgreSQL', 'Docker', 'AWS'],
        'experience': [
            {
                'title': 'Software Engineer',
                'company': 'Tech Company',
                'description': 'Developed web applications using Python and React'
            }
        ],
        'education': [
            {
                'degree': 'Bachelor of Computer Science',
                'school': 'University of Technology'
            }
        ]
    }
    
    try:
        generator = CoverLetterGenerator()
        request = CoverLetterRequest(
            job_data=job_data,
            user_profile=user_profile,
            tone=tone,
            length=length
        )
        
        # Note: This is a sync function calling async, would need proper async handling in real usage
        response = asyncio.run(generator.generate(request))
        
        click.echo(f"✅ Cover letter generated successfully!")
        click.echo(f"📊 Quality Score: {response.quality_score:.2f}/1.0")
        click.echo(f"⏱️  Generation Time: {response.generation_time:.2f}s")
        click.echo(f"🔢 Tokens Used: {response.tokens_used}")
        click.echo("\n" + "=" * 50)
        click.echo("COVER LETTER:")
        click.echo("=" * 50)
        click.echo(response.content)
        
    except Exception as e:
        click.echo(f"❌ Error generating cover letter: {e}")


@cli.command()
def test_config():
    """Test configuration and API connections."""
    click.echo("🔧 Testing AutoApply AI configuration...")
    click.echo("=" * 50)
    
    # Test database URL
    if settings.database_url:
        click.echo("✅ Database URL configured")
    else:
        click.echo("❌ Database URL not configured")
    
    # Test OpenAI API key
    if settings.openai_api_key:
        click.echo("✅ OpenAI API key configured")
        try:
            import openai
            client = openai.OpenAI(api_key=settings.openai_api_key)
            # Test with a simple completion
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=5
            )
            click.echo("✅ OpenAI API connection successful")
        except Exception as e:
            click.echo(f"❌ OpenAI API connection failed: {e}")
    else:
        click.echo("❌ OpenAI API key not configured")
    
    # Test LinkedIn credentials
    if settings.linkedin_email and settings.linkedin_password:
        click.echo("✅ LinkedIn credentials configured")
    else:
        click.echo("⚠️  LinkedIn credentials not configured (optional)")
    
    # Test Redis URL
    if settings.redis_url:
        click.echo("✅ Redis URL configured")
        try:
            import redis
            r = redis.from_url(settings.redis_url)
            r.ping()
            click.echo("✅ Redis connection successful")
        except Exception as e:
            click.echo(f"❌ Redis connection failed: {e}")
    else:
        click.echo("❌ Redis URL not configured")


@cli.command()
def init_db():
    """Initialize the database with tables."""
    click.echo("🗄️  Initializing database...")
    
    try:
        from .database import engine, Base
        Base.metadata.create_all(bind=engine)
        click.echo("✅ Database tables created successfully")
    except Exception as e:
        click.echo(f"❌ Database initialization failed: {e}")


if __name__ == '__main__':
    cli() 