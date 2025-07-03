"""AI-powered cover letter generator using OpenAI GPT-4."""

import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

import openai
from loguru import logger

from ..app.config import settings
from ..scrapers.base_scraper import JobData


@dataclass
class CoverLetterRequest:
    """Request data for cover letter generation."""
    job_data: JobData
    user_profile: Dict[str, Any]
    tone: str = "professional"  # professional, enthusiastic, casual, mission-driven
    length: str = "medium"  # short, medium, long
    focus_areas: Optional[List[str]] = None  # specific areas to emphasize
    custom_instructions: Optional[str] = None


@dataclass
class CoverLetterResponse:
    """Response from cover letter generation."""
    content: str
    tone: str
    length: str
    model_used: str
    tokens_used: int
    generation_time: float
    quality_score: float  # Internal assessment of quality


class CoverLetterGenerator:
    """Generate personalized cover letters using OpenAI GPT-4."""
    
    def __init__(self):
        self.client = openai.OpenAI(api_key=settings.openai_api_key)
        self.model = settings.openai_model
        self.max_tokens = settings.openai_max_tokens
        self.temperature = settings.openai_temperature
        
    async def generate(self, request: CoverLetterRequest) -> CoverLetterResponse:
        """Generate a personalized cover letter."""
        start_time = time.time()
        
        try:
            # Build the prompt
            system_prompt = self._build_system_prompt(request.tone, request.length)
            user_prompt = self._build_user_prompt(request)
            
            logger.info(f"Generating cover letter for {request.job_data.company} - {request.job_data.title}")
            
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                presence_penalty=0.1,
                frequency_penalty=0.1
            )
            
            # Extract the generated content
            content = response.choices[0].message.content.strip()
            tokens_used = response.usage.total_tokens
            generation_time = time.time() - start_time
            
            # Assess quality
            quality_score = self._assess_quality(content, request)
            
            logger.info(
                f"Cover letter generated in {generation_time:.2f}s, "
                f"{tokens_used} tokens, quality: {quality_score:.2f}"
            )
            
            return CoverLetterResponse(
                content=content,
                tone=request.tone,
                length=request.length,
                model_used=self.model,
                tokens_used=tokens_used,
                generation_time=generation_time,
                quality_score=quality_score
            )
            
        except Exception as e:
            logger.error(f"Failed to generate cover letter: {e}")
            raise
            
    def _build_system_prompt(self, tone: str, length: str) -> str:
        """Build the system prompt based on tone and length preferences."""
        
        tone_instructions = {
            "professional": "Write in a professional, formal tone. Be respectful and business-like.",
            "enthusiastic": "Write with enthusiasm and energy. Show genuine excitement about the opportunity.",
            "casual": "Write in a friendly, conversational tone while maintaining professionalism.",
            "mission-driven": "Emphasize alignment with the organization's mission and values. Show passion for their cause."
        }
        
        length_instructions = {
            "short": "Keep the cover letter concise - aim for 2-3 short paragraphs (150-200 words).",
            "medium": "Write a standard cover letter - 3-4 paragraphs (250-350 words).",
            "long": "Write a comprehensive cover letter - 4-5 paragraphs (400-500 words)."
        }
        
        return f"""You are an expert cover letter writer with years of experience helping job seekers land their dream jobs. Your cover letters are known for being:

1. Highly personalized to both the job and the candidate
2. Compelling and engaging from the first sentence
3. Focused on value proposition and achievements
4. Professional yet authentic
5. Free of clichés and generic phrases

TONE: {tone_instructions.get(tone, tone_instructions['professional'])}

LENGTH: {length_instructions.get(length, length_instructions['medium'])}

STRUCTURE GUIDELINES:
- Opening: Hook with genuine connection to company/role
- Body: 1-2 paragraphs highlighting relevant experience and achievements with specific examples
- Closing: Call to action and professional sign-off

REQUIREMENTS:
- Always address the hiring manager by name if provided, otherwise use "Dear Hiring Manager"
- Include specific details from the job description
- Reference the candidate's relevant experience and skills
- Include 1-2 quantified achievements when possible
- Show knowledge of the company/organization
- End with a professional closing and the candidate's name
- Never use placeholder text like [Your Name] or [Company Name]
- Avoid overused phrases like "I am writing to express my interest"

FORMAT: Return only the cover letter content, properly formatted with line breaks between paragraphs."""

    def _build_user_prompt(self, request: CoverLetterRequest) -> str:
        """Build the user prompt with job and profile information."""
        
        job = request.job_data
        profile = request.user_profile
        
        # Extract relevant information from profile
        name = profile.get('full_name', 'John Doe')
        skills = profile.get('skills', [])
        experience = profile.get('experience', [])
        education = profile.get('education', [])
        
        # Build experience summary
        experience_summary = ""
        if experience:
            for exp in experience[:3]:  # Include top 3 experiences
                title = exp.get('title', '')
                company = exp.get('company', '')
                description = exp.get('description', '')
                if title and company:
                    experience_summary += f"- {title} at {company}: {description}\n"
        
        # Build skills list
        skills_list = ", ".join(skills[:10]) if skills else "Various technical skills"
        
        # Build education summary
        education_summary = ""
        if education:
            for edu in education:
                degree = edu.get('degree', '')
                school = edu.get('school', '')
                if degree and school:
                    education_summary += f"- {degree} from {school}\n"
        
        # Add custom instructions if provided
        custom_section = ""
        if request.custom_instructions:
            custom_section = f"\n\nSPECIAL INSTRUCTIONS:\n{request.custom_instructions}"
        
        # Add focus areas if provided
        focus_section = ""
        if request.focus_areas:
            focus_section = f"\n\nFOCUS AREAS (emphasize these): {', '.join(request.focus_areas)}"
        
        return f"""Please write a personalized cover letter for this job application:

JOB INFORMATION:
- Position: {job.title}
- Company: {job.company}
- Location: {job.location}
- Job Description: {job.description[:1000]}...  # Truncated for token limit
- Requirements: {job.requirements[:500]}...  # Truncated for token limit

CANDIDATE INFORMATION:
- Name: {name}
- Top Skills: {skills_list}

WORK EXPERIENCE:
{experience_summary}

EDUCATION:
{education_summary}

{focus_section}{custom_section}

Generate a compelling cover letter that connects this candidate's background to this specific opportunity."""

    def _assess_quality(self, content: str, request: CoverLetterRequest) -> float:
        """Assess the quality of the generated cover letter."""
        score = 0.0
        max_score = 10.0
        
        # Check for basic requirements
        if request.job_data.company.lower() in content.lower():
            score += 1.0  # Company name mentioned
            
        if request.job_data.title.lower() in content.lower():
            score += 1.0  # Job title mentioned
            
        if len(content.split()) >= 150:
            score += 1.0  # Adequate length
            
        if "Dear" in content:
            score += 0.5  # Professional greeting
            
        if "Sincerely" in content or "Best regards" in content:
            score += 0.5  # Professional closing
            
        # Check for personalization
        profile_skills = request.user_profile.get('skills', [])
        if any(skill.lower() in content.lower() for skill in profile_skills[:5]):
            score += 2.0  # Skills mentioned
            
        # Check for specific examples/achievements
        if any(word in content for word in ['achieved', 'led', 'managed', 'increased', 'improved']):
            score += 1.0  # Action verbs present
            
        # Check for numbers/quantification
        import re
        if re.search(r'\d+[%$]|\d+\s+(years?|months?|percent)', content):
            score += 1.0  # Quantified achievements
            
        # Avoid common clichés
        cliches = [
            'i am writing to express my interest',
            'please find my resume attached',
            'i would be a great fit',
            'i am passionate about'
        ]
        if not any(cliche in content.lower() for cliche in cliches):
            score += 1.0  # No major clichés
            
        # Length appropriateness
        word_count = len(content.split())
        target_ranges = {
            'short': (150, 250),
            'medium': (250, 400),
            'long': (400, 600)
        }
        
        target_range = target_ranges.get(request.length, target_ranges['medium'])
        if target_range[0] <= word_count <= target_range[1]:
            score += 1.0  # Appropriate length
            
        return min(score, max_score) / max_score  # Normalize to 0-1
        
    async def generate_multiple_variations(
        self,
        request: CoverLetterRequest,
        count: int = 3
    ) -> List[CoverLetterResponse]:
        """Generate multiple variations of a cover letter."""
        variations = []
        
        # Generate different variations by adjusting temperature and focus
        temperatures = [0.5, 0.7, 0.9]
        
        for i in range(count):
            # Slightly modify the request for variation
            varied_request = CoverLetterRequest(
                job_data=request.job_data,
                user_profile=request.user_profile,
                tone=request.tone,
                length=request.length,
                focus_areas=request.focus_areas,
                custom_instructions=request.custom_instructions
            )
            
            # Temporarily adjust temperature for variation
            original_temp = self.temperature
            self.temperature = temperatures[i % len(temperatures)]
            
            try:
                variation = await self.generate(varied_request)
                variations.append(variation)
            except Exception as e:
                logger.warning(f"Failed to generate variation {i+1}: {e}")
            finally:
                self.temperature = original_temp
                
        return variations
        
    def get_tone_suggestions(self, job_data: JobData) -> List[str]:
        """Suggest appropriate tones based on job description."""
        description_lower = job_data.description.lower()
        company_lower = job_data.company.lower()
        
        suggestions = []
        
        # Mission-driven for nonprofits, social causes
        if any(word in description_lower + company_lower for word in [
            'nonprofit', 'mission', 'social impact', 'community', 'charity', 'foundation'
        ]):
            suggestions.append('mission-driven')
            
        # Enthusiastic for startups, creative roles
        if any(word in description_lower for word in [
            'startup', 'creative', 'innovative', 'dynamic', 'fast-paced'
        ]):
            suggestions.append('enthusiastic')
            
        # Professional for traditional industries
        if any(word in description_lower + company_lower for word in [
            'finance', 'consulting', 'law', 'banking', 'corporate'
        ]):
            suggestions.append('professional')
        else:
            suggestions.append('professional')  # Default
            
        # Casual for tech, modern companies
        if any(word in description_lower + company_lower for word in [
            'tech', 'software', 'startup', 'remote', 'flexible'
        ]):
            suggestions.append('casual')
            
        return list(set(suggestions))  # Remove duplicates 