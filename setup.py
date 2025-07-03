#!/usr/bin/env python3
"""Setup script for AutoApply AI."""

import os
import sys
import subprocess
import shutil
from pathlib import Path


def run_command(command, description=""):
    """Run a shell command and handle errors."""
    print(f"\n{'='*60}")
    print(f"Running: {description or command}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(
            command,
            shell=True,
            check=True,
            capture_output=True,
            text=True
        )
        
        if result.stdout:
            print(result.stdout)
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {command}")
        print(f"Exit code: {e.returncode}")
        if e.stdout:
            print(f"stdout: {e.stdout}")
        if e.stderr:
            print(f"stderr: {e.stderr}")
        return False


def check_requirements():
    """Check if required software is installed."""
    print("\n🔍 Checking system requirements...")
    
    requirements = {
        "python3": "Python 3.8+",
        "pip": "pip package manager",
        "docker": "Docker",
        "docker-compose": "Docker Compose"
    }
    
    missing = []
    
    for cmd, desc in requirements.items():
        if not shutil.which(cmd):
            missing.append(f"❌ {desc} ({cmd})")
        else:
            print(f"✅ {desc} found")
    
    if missing:
        print("\n❌ Missing requirements:")
        for item in missing:
            print(f"  {item}")
        print("\nPlease install the missing requirements and run setup again.")
        return False
    
    return True


def create_directories():
    """Create necessary directories."""
    print("\n📁 Creating directories...")
    
    directories = [
        "uploads",
        "logs",
        "data",
        "backend/app/services/templates"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✅ Created directory: {directory}")


def setup_environment():
    """Set up Python environment and install dependencies."""
    print("\n🐍 Setting up Python environment...")
    
    # Create virtual environment if it doesn't exist
    if not Path("venv").exists():
        if not run_command("python3 -m venv venv", "Creating virtual environment"):
            return False
    
    # Determine activation command based on OS
    if sys.platform == "win32":
        activate_cmd = "venv\\Scripts\\activate"
        pip_cmd = "venv\\Scripts\\pip"
    else:
        activate_cmd = "source venv/bin/activate"
        pip_cmd = "venv/bin/pip"
    
    # Install dependencies
    commands = [
        f"{pip_cmd} install --upgrade pip",
        f"{pip_cmd} install -r requirements.txt",
        f"{pip_cmd} install playwright",
        "playwright install chromium"
    ]
    
    for cmd in commands:
        if not run_command(cmd, f"Installing dependencies: {cmd}"):
            return False
    
    return True


def create_env_file():
    """Create .env file from template if it doesn't exist."""
    print("\n⚙️  Setting up environment configuration...")
    
    env_file = Path(".env")
    
    if env_file.exists():
        print("✅ .env file already exists")
        return True
    
    # Create .env file with template
    env_template = """# AutoApply AI Environment Configuration

# Database
DATABASE_URL=postgresql://autoapply:password@localhost:5432/autoapply_ai

# Security
SECRET_KEY=your-secret-key-change-this-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# OpenAI Configuration
OPENAI_API_KEY=your-openai-api-key-here
OPENAI_MODEL=gpt-4-turbo-preview

# LinkedIn Configuration
LINKEDIN_EMAIL=your-linkedin-email@example.com
LINKEDIN_PASSWORD=your-linkedin-password

# SMTP Configuration
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
FROM_EMAIL=your-email@gmail.com
FROM_NAME=AutoApply AI

# Redis Configuration
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Application Settings
DEBUG=True
LOG_LEVEL=INFO
HOST=0.0.0.0
PORT=8000

# File Upload Settings
UPLOAD_DIR=uploads/
MAX_FILE_SIZE=10485760

# Scraping Settings
HEADLESS_BROWSER=True
SCRAPING_DELAY=2
MAX_APPLICATIONS_PER_DAY=20

# Dashboard Settings
DASHBOARD_ITEMS_PER_PAGE=20
"""
    
    with open(env_file, "w") as f:
        f.write(env_template)
    
    print("✅ Created .env file")
    print("⚠️  Please edit .env file with your actual configuration values")
    
    return True


def setup_docker():
    """Set up Docker services."""
    print("\n🐳 Setting up Docker services...")
    
    # Check if Docker is running
    if not run_command("docker info", "Checking Docker status"):
        print("❌ Docker is not running. Please start Docker and try again.")
        return False
    
    # Pull and start services
    commands = [
        "docker-compose pull",
        "docker-compose up -d postgres redis"
    ]
    
    for cmd in commands:
        if not run_command(cmd, f"Docker setup: {cmd}"):
            return False
    
    print("✅ Docker services started")
    return True


def initialize_database():
    """Initialize the database."""
    print("\n🗄️  Initializing database...")
    
    # Wait for database to be ready
    print("Waiting for database to be ready...")
    if not run_command("sleep 5", "Waiting for database"):
        return False
    
    # Initialize database
    if sys.platform == "win32":
        python_cmd = "venv\\Scripts\\python"
    else:
        python_cmd = "venv/bin/python"
    
    if not run_command(f"{python_cmd} -m backend.app.database_init", "Initializing database"):
        return False
    
    print("✅ Database initialized")
    return True


def run_tests():
    """Run basic tests to ensure setup is working."""
    print("\n🧪 Running basic tests...")
    
    if sys.platform == "win32":
        python_cmd = "venv\\Scripts\\python"
    else:
        python_cmd = "venv/bin/python"
    
    # Test database connection
    test_script = """
import sys
sys.path.append('.')
from backend.app.database import engine
from sqlalchemy import text

try:
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        print("✅ Database connection successful")
except Exception as e:
    print(f"❌ Database connection failed: {e}")
    sys.exit(1)
"""
    
    with open("test_db.py", "w") as f:
        f.write(test_script)
    
    success = run_command(f"{python_cmd} test_db.py", "Testing database connection")
    
    # Clean up test file
    Path("test_db.py").unlink(missing_ok=True)
    
    return success


def main():
    """Main setup function."""
    print("🚀 AutoApply AI Setup Script")
    print("=" * 60)
    
    steps = [
        ("Checking requirements", check_requirements),
        ("Creating directories", create_directories),
        ("Setting up environment", setup_environment),
        ("Creating .env file", create_env_file),
        ("Setting up Docker", setup_docker),
        ("Initializing database", initialize_database),
        ("Running tests", run_tests)
    ]
    
    failed_steps = []
    
    for step_name, step_func in steps:
        try:
            if not step_func():
                failed_steps.append(step_name)
        except Exception as e:
            print(f"❌ Error in {step_name}: {e}")
            failed_steps.append(step_name)
    
    print("\n" + "=" * 60)
    print("SETUP SUMMARY")
    print("=" * 60)
    
    if failed_steps:
        print("❌ Setup completed with errors:")
        for step in failed_steps:
            print(f"  - {step}")
        print("\nPlease fix the errors and run setup again.")
        return False
    else:
        print("✅ Setup completed successfully!")
        print("\nNext steps:")
        print("1. Edit .env file with your actual configuration")
        print("2. Add your OpenAI API key to .env")
        print("3. Run: ./start.sh")
        print("4. Open http://localhost:8000 in your browser")
        return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 