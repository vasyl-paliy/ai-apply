# AutoApply AI - Quick Start Guide

🚀 **Get your automated job application system running in 5 minutes!**

## ⚡ Quick Setup

### 1. Prerequisites
- [Docker](https://www.docker.com/get-started) and Docker Compose
- [OpenAI API Key](https://platform.openai.com/api-keys) (required)
- LinkedIn credentials (optional but recommended)

### 2. Clone and Configure
```bash
# Clone the repository (or use your existing setup)
# cd job-hunt

# Copy environment template
cp .env.example .env

# Edit .env with your API keys
nano .env  # or your preferred editor
```

**Required Configuration:**
- `OPENAI_API_KEY` - Your OpenAI API key
- `SECRET_KEY` - Generate a secure secret key

**Optional but Recommended:**
- `LINKEDIN_EMAIL` and `LINKEDIN_PASSWORD` - For LinkedIn job scraping
- `GMAIL_*` settings - For email applications

### 3. Start the System
```bash
# Make startup script executable (if not already)
chmod +x start.sh

# Run the startup script
./start.sh
```

### 4. Access the System
- 📖 **API Documentation**: http://localhost:8000/docs
- 🌐 **Main API**: http://localhost:8000
- 🌸 **Task Monitor**: http://localhost:5555 (Flower)
- 🗄️ **Database Admin**: http://localhost:5050 (pgAdmin)

## 🧪 Test the System

### Test Configuration
```bash
docker-compose exec backend python -m backend.app.cli test-config
```

### Search for Jobs
```bash
docker-compose exec backend python -m backend.app.cli search-jobs \
  --keywords "python developer" \
  --keywords "backend engineer" \
  --locations "San Francisco" \
  --max-results 5
```

### Generate a Cover Letter
```bash
docker-compose exec backend python -m backend.app.cli generate-cover-letter \
  --job-title "Senior Python Developer" \
  --company "Tech Startup Inc" \
  --job-description "We're looking for a senior Python developer to join our team..." \
  --name "Your Name" \
  --tone "enthusiastic"
```

## 📚 How It Works

### 1. **Job Scraping Pipeline**
```
LinkedIn/Indeed → JobPosting Database → Matching Algorithm → User Review
```

### 2. **Cover Letter Generation**
```
Job Description + User Profile → GPT-4 → Personalized Cover Letter → Quality Check
```

### 3. **Application Workflow**
```
Approved Jobs → Generate Cover Letter → Send Email/Apply → Track Status → Follow-up
```

## 🔧 API Examples

### Search Jobs via API
```bash
curl -X POST http://localhost:8000/api/v1/jobs/search \
  -H "Content-Type: application/json" \
  -d '{
    "keywords": ["python", "developer"],
    "locations": ["Remote"],
    "max_results": 10
  }'
```

### Get Job Statistics
```bash
curl http://localhost:8000/api/v1/jobs/stats/summary
```

## 📁 Project Structure

```
job-hunt/
├── README.md              # Full documentation
├── QUICKSTART.md          # This file
├── requirements.txt       # Python dependencies
├── docker-compose.yml     # Docker services
├── Dockerfile            # Container configuration
├── start.sh              # Quick startup script
├── .env.example          # Environment template
│
├── backend/              # Main application
│   ├── app/             # FastAPI application
│   │   ├── main.py      # API server
│   │   ├── config.py    # Settings
│   │   ├── database.py  # Database connection
│   │   ├── models.py    # SQLAlchemy models
│   │   ├── cli.py       # Command-line interface
│   │   └── routers/     # API endpoints
│   │
│   ├── scrapers/        # Job scraping
│   │   ├── base_scraper.py      # Base scraper class
│   │   └── linkedin_scraper.py  # LinkedIn implementation
│   │
│   └── generators/      # AI content generation
│       └── cover_letter_generator.py  # GPT-4 cover letters
```

## 🔄 Daily Workflow

1. **Morning (8 AM)**: System scrapes new jobs
2. **Morning (8:30 AM)**: AI matches jobs to your profile
3. **Morning (9 AM)**: Cover letters generated for top matches
4. **Day (9 AM - 6 PM)**: You review and approve applications
5. **Evening (6 PM)**: Approved applications are sent
6. **Next Day**: Follow-up contacts are found and outreach prepared

## 🛠️ Customization

### Add New Job Sources
1. Create a new scraper in `backend/scrapers/`
2. Inherit from `BaseScraper`
3. Implement `search_jobs()` and `get_job_details()`
4. Register in the job search API

### Customize Cover Letters
- Modify prompts in `cover_letter_generator.py`
- Add new tones and styles
- Implement company-specific templates
- Add industry-specific optimizations

### Add New Application Methods
- Email integration (Gmail API)
- Job portal automation (Playwright)
- ATS system integration
- Social media outreach (LinkedIn)

## 🔐 Security & Privacy

- All API keys stored in environment variables
- Database connections encrypted
- No sensitive data in logs
- Optional human approval for all actions
- Data encrypted at rest

## 🚨 Troubleshooting

### Common Issues

**"Database connection failed"**
```bash
# Restart database
docker-compose restart postgres
# Check logs
docker-compose logs postgres
```

**"OpenAI API error"**
```bash
# Test API key
docker-compose exec backend python -c "import openai; print('API key valid' if openai.api_key else 'No API key')"
```

**"LinkedIn scraping blocked"**
```bash
# Try with different user agent
# Add delays between requests
# Use residential proxy (advanced)
```

**"Container won't start"**
```bash
# Check Docker resources
docker system df
# Clean up
docker system prune
# Rebuild
docker-compose build --no-cache
```

### Get Help
- Check logs: `docker-compose logs -f`
- Test config: `./test-config.sh`
- Join discussions: GitHub Issues
- Email: support@autoapply.ai

## 🚀 Next Steps

1. **Configure your profile**: Add resume, skills, preferences
2. **Set up integrations**: Gmail, LinkedIn, job boards
3. **Customize templates**: Cover letter styles, follow-up messages
4. **Enable automation**: Set daily schedules, approval workflows
5. **Monitor performance**: Track application success rates
6. **Scale up**: Add more job sources, AI models, team features

---

**Need help?** Check the full [README.md](README.md) or create an issue on GitHub.

**Ready to automate your job hunt?** Run `./start.sh` and let AutoApply AI handle the tedious work while you focus on landing your dream job! 🎯 