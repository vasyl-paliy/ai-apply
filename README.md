# AutoApply AI - Automated Job Application Agent

An intelligent agent that automates job searching, application generation, and submission while maintaining human oversight and control.

## 🧠 Overview

AutoApply AI is a comprehensive job application automation system that:

- **Scrapes job postings** from multiple sources based on your preferences
- **Parses and matches** job descriptions to your resume/profile
- **Generates tailored cover letters** using advanced LLMs
- **Submits applications** via email or job portals
- **Finds relevant contacts** for follow-up
- **Tracks application status** in a centralized dashboard
- **Runs on schedule** with automated summaries

## 🚀 Features

### Core Components
- **Job Scraper**: Multi-source job discovery (LinkedIn, Indeed, Idealist, etc.)
- **Resume Parser**: Extract and structure your skills and experience
- **Cover Letter Generator**: AI-powered personalized cover letters
- **Application Engine**: Automated email and portal submissions
- **Follow-up Finder**: Contact discovery for networking
- **Tracker Dashboard**: Centralized application management
- **Scheduler**: Background processing with reports

### Key Benefits
- ✅ Eliminate repetitive job application tasks
- ✅ Maintain personalization at scale
- ✅ Never miss application deadlines
- ✅ Consistent follow-up scheduling
- ✅ Comprehensive application tracking
- ✅ Human oversight and approval workflows

## 🛠️ Tech Stack

| Component | Technology |
|-----------|------------|
| Backend | Python + FastAPI |
| Task Queue | Celery + Redis |
| Database | PostgreSQL |
| LLM | OpenAI GPT-4 Turbo |
| Web Scraping | Playwright |
| Email | Gmail API |
| Dashboard | React + TypeScript |
| Hosting | Docker + Railway/Render |

## 🏗️ Architecture

```
AutoApply AI/
├── backend/              # FastAPI application
│   ├── app/             # Core application logic
│   ├── scrapers/        # Job scraping modules
│   ├── generators/      # Cover letter generation
│   ├── applicators/     # Application submission
│   └── trackers/        # Status tracking
├── frontend/            # React dashboard
├── workers/             # Background task workers
├── config/              # Configuration files
├── tests/               # Test suites
└── docs/                # Documentation
```

## 📦 Installation

### Prerequisites
- Python 3.9+
- Node.js 16+
- PostgreSQL
- Redis
- Docker (optional)

### Setup

1. **Clone and setup environment:**
```bash
git clone <repository-url>
cd job-hunt
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. **Configure environment variables:**
```bash
cp .env.example .env
# Edit .env with your API keys and configuration
```

3. **Setup database:**
```bash
# Install PostgreSQL and create database
createdb autoapply_ai
python -m alembic upgrade head
```

4. **Start services:**
```bash
# Start Redis
redis-server

# Start main application
python -m uvicorn backend.app.main:app --reload

# Start background workers
celery -A backend.app.worker worker --loglevel=info

# Start frontend (in separate terminal)
cd frontend
npm install
npm start
```

## 🎯 Usage

### Quick Start

1. **Configure your profile:**
   - Upload your resume (PDF/DOCX)
   - Set job preferences (location, keywords, salary range)
   - Configure notification preferences

2. **Set up integrations:**
   - Connect Gmail for email applications
   - Add LinkedIn credentials (optional)
   - Configure job board preferences

3. **Run your first job search:**
   ```bash
   python -m backend.app.cli search --keywords "nonprofit arts" --location "Providence, RI"
   ```

4. **Review and approve applications:**
   - Check the dashboard for new matches
   - Review generated cover letters
   - Approve applications for submission

### Advanced Usage

#### Custom Job Queries
```python
from backend.app.scrapers import JobScraper

scraper = JobScraper()
jobs = scraper.search(
    keywords=["nonprofit", "arts", "program coordinator"],
    locations=["Providence, RI", "Boston, MA"],
    job_types=["full-time", "hybrid"],
    salary_min=50000
)
```

#### Cover Letter Customization
```python
from backend.app.generators import CoverLetterGenerator

generator = CoverLetterGenerator()
cover_letter = generator.generate(
    job_description=job_desc,
    resume_data=resume,
    tone="mission-driven",
    length="concise"
)
```

## 🔧 Configuration

### Environment Variables
```env
# OpenAI API
OPENAI_API_KEY=your_openai_key

# Database
DATABASE_URL=postgresql://user:pass@localhost/autoapply_ai

# Email
GMAIL_CLIENT_ID=your_gmail_client_id
GMAIL_CLIENT_SECRET=your_gmail_client_secret

# Job Boards
LINKEDIN_EMAIL=your_linkedin_email
LINKEDIN_PASSWORD=your_linkedin_password

# Notifications
SLACK_WEBHOOK_URL=your_slack_webhook
```

### Job Search Preferences
```yaml
# config/job_preferences.yaml
keywords:
  - nonprofit
  - arts
  - program coordinator
  - community outreach

locations:
  - Providence, RI
  - Boston, MA
  - Remote

job_types:
  - full-time
  - hybrid

salary_range:
  min: 45000
  max: 75000

industries:
  - nonprofit
  - arts
  - education
```

## 🔄 Workflows

### Daily Automation
1. **Morning Scrape** (8 AM): Find new job postings
2. **Matching** (8:30 AM): Score jobs against your profile
3. **Generation** (9 AM): Create cover letters for top matches
4. **Review Period** (9 AM - 6 PM): Human approval window
5. **Submission** (6 PM): Send approved applications
6. **Follow-up** (Next day): Find contacts and prepare outreach

### Weekly Reports
- Application statistics
- Response rates
- New opportunities
- Follow-up reminders

## 📊 Dashboard Features

- **Job Pipeline**: Visual pipeline from discovery to offer
- **Application Status**: Real-time tracking
- **Cover Letter Library**: Reusable templates and examples
- **Contact Management**: Networking and follow-up tracking
- **Analytics**: Success metrics and optimization insights

## 🧪 Testing

```bash
# Run all tests
pytest

# Run specific test suites
pytest tests/test_scrapers.py
pytest tests/test_generators.py
pytest tests/test_applicators.py

# Run with coverage
pytest --cov=backend
```

## 🚀 Deployment

### Docker Deployment
```bash
docker-compose up -d
```

### Production Deployment
```bash
# Deploy to Railway/Render
railway up
# or
render deploy
```

## 📈 Roadmap

### Phase 1 (MVP) - Weeks 1-2
- [x] Basic job scraping
- [x] Resume parsing
- [x] Cover letter generation
- [x] Email applications
- [x] Simple dashboard

### Phase 2 - Weeks 3-4
- [ ] Portal automation
- [ ] Contact finding
- [ ] Advanced matching
- [ ] Mobile notifications

### Phase 3 - Weeks 5-6
- [ ] Browser extension
- [ ] Advanced analytics
- [ ] Team collaboration
- [ ] API access

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📜 License

MIT License - see LICENSE file for details

## 🆘 Support

- **Issues**: GitHub Issues
- **Discussions**: GitHub Discussions
- **Email**: support@autoapply.ai

---

Built with ❤️ for job seekers who want to focus on what matters most. 