import os
import anthropic
import openai
import google.generativeai as genai
from typing import List, Dict


class CommentGenerator:
    """
    Arbitrage Comment Engine - Generates 3 clinical comment options
    for LinkedIn posts/comments using persona and archived posts for calibration.
    """
    
    def __init__(self, persona_bio, archived_posts):
        self.persona = persona_bio
        self.archived_posts = archived_posts
        
        # Initialize API clients
        self.claude_client = anthropic.Anthropic(
            api_key=os.environ.get("ANTHROPIC_API_KEY")
        )
        self.openai_client = openai.OpenAI(
            api_key=os.environ.get("OPENAI_API_KEY")
        )
        genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
        
        self.base_prompt = self._build_base_prompt()
    
    def _build_base_prompt(self) -> str:
        """
        Build the base prompt with persona and tone calibration.
        """
        # Get top 3 archived posts for tone calibration
        # Prioritize by high_value_engagement, then clarity_rating
        top_posts = sorted(
            self.archived_posts[:10],  # Consider top 10, then pick best 3
            key=lambda p: (
                p.high_value_engagement * 10 + 
                (p.clarity_rating or 0) + 
                p.linkedin_saves
            ),
            reverse=True
        )[:3]
        
        tone_calibration = "\n\n".join([
            f"REFERENCE POST {i+1} ({post.published_date}, HV Eng: {post.high_value_engagement}):\n{post.content[:400]}..."
            for i, post in enumerate(top_posts)
        ]) if top_posts else "No archived posts available for calibration."
        
        prompt = f"""You are generating LinkedIn comments for a {self.persona.professional_title} using the CLINICAL SOVEREIGN framework.

THE CLINICAL SOVEREIGN PERSONA (Optimized Structure):

I. THE ENGINE (Physics - 35% Weight)
- Axiomatic Logic: Fidelity to Reality. Filter through First Principles.
- Structural Ruthlessness: Attack the System ("The Villain"), never the person.
- Core Expertise: {self.persona.core_expertise}

II. THE ARMOR (Zero-Kelvin - 25% Weight)
- Zero Ego/Anger: Total detachment. No complaining, no emotional language.
- Benevolent Disinterest: Helpful, but not "involved."
- FORBIDDEN TERMS: {self.persona.forbidden_terms}

III. THE WEAPON (The Verdict - 20% Weight)
- High-Density Output: Verdicts, not opinions. Precise. Visceral.
- Slightly Venomous: Toxic to mediocrity, oxygen to competence.
- Writing Axioms: {self.persona.writing_axioms}

IV. THE KINETIC (Action - Critical)
- Artifacts: Logic must produce a "Third Object" (framework, system, structure).
- Velocity: Execution speed. No slow, thoughtful meandering.
- Target Audience: {self.persona.target_audience}

TONE CALIBRATION (Your Best-Performing Comments/Posts):
{tone_calibration}

COMMENT GENERATION RULES:
1. Physics Engine: Use First Principles. Structural logic, not opinions.
2. Zero-Kelvin Shield: Zero emotional language. Total detachment.
3. Verdict Output: High-density signal. Precise verdicts.
4. Slightly Venomous: Toxic to mediocrity, oxygen to competence.
5. Kinetic Artifact: Produce a framework/system/structure (the "Third Object").
6. Velocity: Execute immediately. 2-4 sentences max.

You will generate 3 comment options with different strategic angles:
- Option 1: Analytical/Structural angle (Physics Engine - systems analysis through First Principles)
- Option 2: Framework/Model angle (Kinetic Artifact - introduce a conceptual framework/system)
- Option 3: Counterpoint/Refinement angle (Structural Villain - attack the system, not the person)

Each option must be:
- Axiomatically sound (Physics Engine)
- Zero-Kelvin (no emotional language)
- High-density verdict (not opinion)
- Slightly venomous to mediocrity
- Produce an artifact (framework/system/structure)
- Tone-matched to your archived high-performing content

ORIGINAL POST/COMMENT TO RESPOND TO:
"""
        return prompt
    
    def _generate_with_claude(self, source_text: str, angle: str) -> str:
        """Generate comment using Claude."""
        try:
            angle_prompt = f"""

Generate Option {angle}.

CRITICAL: Output ONLY the comment text itself. No explanations, no prefixes, no markdown. Just write the complete comment as you would post it on LinkedIn (2-4 sentences).

Comment:"""
            full_prompt = self.base_prompt + source_text + angle_prompt
            
            message = self.claude_client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1000,  # Increased from 500 to ensure complete comments
                temperature=0.4,
                messages=[{
                    "role": "user",
                    "content": full_prompt
                }]
            )
            text = message.content[0].text.strip()
            # Remove any prefixes Claude might add
            if text.startswith("Comment:"):
                text = text[8:].strip()
            return text
        except Exception as e:
            return f"Claude generation failed: {str(e)}"
    
    def _generate_with_gpt(self, source_text: str, angle: str) -> str:
        """Generate comment using GPT-4."""
        try:
            angle_prompt = f"""

Generate Option {angle}.

CRITICAL: Output ONLY the comment text itself. No explanations, no prefixes, no markdown. Just write the complete comment as you would post it on LinkedIn (2-4 sentences).

Comment:"""
            full_prompt = self.base_prompt + source_text + angle_prompt
            
            response = self.openai_client.chat.completions.create(
                model="gpt-5.2-2025-12-11",
                messages=[
                    {"role": "system", "content": "You are a clinical, analytical comment generator for LinkedIn. Output only the comment text, nothing else."},
                    {"role": "user", "content": full_prompt}
                ],
                temperature=0.4,
                max_completion_tokens=1000  # Use max_completion_tokens to avoid unsupported parameter error
            )
            text = response.choices[0].message.content.strip()
            # Remove any prefixes GPT might add
            if text.startswith("Comment:"):
                text = text[8:].strip()
            return text
        except Exception as e:
            return f"GPT generation failed: {str(e)}"
    
    def _generate_with_gemini(self, source_text: str, angle: str) -> str:
        """Generate comment using Gemini."""
        try:
            angle_prompt = f"""

Generate Option {angle}.

CRITICAL: Output ONLY the comment text itself. No explanations, no prefixes like "Option 3:" or "Comment:", no markdown formatting, no bullet points. Just write the comment as you would post it on LinkedIn. The comment should be 2-4 sentences and complete.

Comment:"""
            full_prompt = self.base_prompt + source_text + angle_prompt
            
            model = genai.GenerativeModel('gemini-3-pro-preview')
            response = model.generate_content(
                full_prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.4,
                    max_output_tokens=1000  # Increased from 500 to prevent truncation
                )
            )
            # Clean up the response
            text = response.text.strip()
            
            # Remove common prefixes that Gemini might add
            prefixes_to_remove = [
                "Option 3:",
                "Comment:",
                "**Option 3:**",
                "**Comment:**",
                "*Option 3:*",
                "*Comment:*"
            ]
            for prefix in prefixes_to_remove:
                if text.startswith(prefix):
                    text = text[len(prefix):].strip()
            
            # Remove markdown formatting
            text = text.replace('**', '').replace('*', '').strip()
            
            return text
        except Exception as e:
            return f"Gemini generation failed: {str(e)}"
    
    def generate_three_options(self, source_text: str) -> Dict[str, str]:
        """
        Generate 3 comment options using different LLMs for diversity.
        Each LLM generates one option with a different strategic angle.
        
        Returns:
            {
                'option_1': str,  # Analytical angle (Claude)
                'option_2': str,  # Framework angle (GPT)
                'option_3': str   # Counterpoint angle (Gemini)
            }
        """
        return {
            'option_1': self._generate_with_claude(
                source_text, 
                "1 (Analytical/Structural - focus on systems and structures)"
            ),
            'option_2': self._generate_with_gpt(
                source_text,
                "2 (Framework/Model - introduce a conceptual framework or model)"
            ),
            'option_3': self._generate_with_gemini(
                source_text,
                "3 (Counterpoint/Refinement - respectful challenge or extension of ideas)"
            )
        }

