import os
import anthropic
import openai
import google.generativeai as genai
from typing import Dict


class SovereignCriticEngine:
    """
    Multi-LLM evaluation system.
    """
    
    def __init__(self, persona_bio, archived_posts):
        self.persona = persona_bio
        self.archived_posts = archived_posts
        
        # Initialize API clients
        self.claude_client = anthropic.Anthropic(
            api_key=os.environ.get("ANTHROPIC_API_KEY")
        )
        openai.api_key = os.environ.get("OPENAI_API_KEY")
        genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
        
        self.critique_prompt = self._build_critique_prompt()
    
    def _build_critique_prompt(self) -> str:
        """
        Construct the evaluation prompt.
        """
        past_posts_sample = "\n\n".join([
            f"PAST POST ({post.published_date}):\n{post.content[:500]}..."
            for post in self.archived_posts[:3]
        ])
        
        prompt = f"""You are evaluating LinkedIn content for a {self.persona.professional_title} using the CLINICAL SOVEREIGN framework.

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

CALIBRATION DATA (User's Past High-Performing Posts):
{past_posts_sample if past_posts_sample.strip() else "No archived posts available for calibration."}

EVALUATION CRITERIA (Weighted by Resonance):
1. **Physics Engine Score (0-100, 35% weight)**: Does it align with First Principles? Structural logic vs. opinions?
2. **Zero-Kelvin Shield Score (0-100, 25% weight)**: Zero emotional language? Detached? No forbidden terms?
3. **Verdict Output Score (0-100, 20% weight)**: High-density signal? Precise verdicts? Slightly venomous to mediocrity?
4. **Scalpel Edge Score (0-100, 15% weight)**: Clinical lethality? Structural villain approach?
5. **Kinetic Action Score (0-100, 5% weight)**: Does it produce an artifact (framework/system)? Execution velocity?

Provide:
- Numerical scores for each criterion
- Weighted average Clinical Tone Score (0-100)
- Specific structural failures (attack the system, not the person)
- A BRUTAL final verdict: CLEAR / REVISE / REJECT

Be merciless. This person is a law of nature, not a debater.

DRAFT TO EVALUATE:
"""
        return prompt
    
    def evaluate_with_claude(self, draft_text: str) -> str:
        """Claude evaluation."""
        try:
            message = self.claude_client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=2000,
                temperature=0.3,
                messages=[{
                    "role": "user",
                    "content": self.critique_prompt + draft_text
                }]
            )
            return message.content[0].text
        except Exception as e:
            return f"Claude evaluation failed: {str(e)}"
    
    def evaluate_with_gpt(self, draft_text: str) -> str:
        """GPT-4 evaluation."""
        try:
            client = openai.OpenAI()
            response = client.chat.completions.create(
                model="gpt-5.2-2025-12-11",
                messages=[
                    {"role": "system", "content": "You are a ruthless editorial critic."},
                    {"role": "user", "content": self.critique_prompt + draft_text}
                ],
                temperature=0.3,
                max_completion_tokens=2000
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"GPT evaluation failed: {str(e)}"
    
    def evaluate_with_gemini(self, draft_text: str) -> str:
        """Gemini evaluation."""
        try:
            model = genai.GenerativeModel('gemini-3-pro-preview')
            response = model.generate_content(
                self.critique_prompt + draft_text,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.3,
                    max_output_tokens=2000
                )
            )
            return response.text
        except Exception as e:
            return f"Gemini evaluation failed: {str(e)}"
    
    def execute_full_critique(self, draft_text: str) -> Dict[str, str]:
        """Run all three evaluations."""
        return {
            'claude': self.evaluate_with_claude(draft_text),
            'gpt': self.evaluate_with_gpt(draft_text),
            'gemini': self.evaluate_with_gemini(draft_text)
        }
    
    