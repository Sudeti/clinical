import os
import anthropic
import openai
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
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
- Structural Precision: Examine the System, never the person.
- Core Expertise: {self.persona.core_expertise}

II. THE ARMOR (Zero-Kelvin - 25% Weight)
- Zero Ego/Anger: Total detachment. No complaining, no emotional language.
- Benevolent Disinterest: Helpful, but not "involved."
- FORBIDDEN TERMS: {self.persona.forbidden_terms}

III. THE WEAPON (The Verdict - 20% Weight)
- High-Density Output: Verdicts, not opinions. Precise. Visceral.
- Elevating Standards: Championing excellence, rewarding competence.
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
4. Elevating Standards: Championing excellence, rewarding competence.
5. Kinetic Artifact: Produce a framework/system/structure (the "Third Object").
6. Velocity: Execute immediately. 2-4 sentences max.

You will generate 3 comment options with different strategic angles:
- Option 1: Analytical/Structural angle (Physics Engine - systems analysis through First Principles)
- Option 2: Framework/Model angle (Kinetic Artifact - introduce a conceptual framework/system)
- Option 3: Counterpoint/Refinement angle (Constructive challenge - examine the system, offer perspective)

Each option must be:
- Axiomatically sound (Physics Engine)
- Zero-Kelvin (no emotional language)
- High-density verdict (not opinion)
- Elevating standards and championing excellence
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
                    max_output_tokens=1000,  # Increased from 500 to prevent truncation
                ),
                safety_settings={
                    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
                }
            )
            
            # Check if response was blocked or has no content
            if not response.candidates or len(response.candidates) == 0:
                return "Gemini generation failed: No candidates returned (content may have been blocked)"
            
            candidate = response.candidates[0]
            if candidate.finish_reason and candidate.finish_reason != 1:  # 1 = STOP (normal), others are issues
                finish_reasons = {
                    2: "SAFETY (content blocked by safety filters)",
                    3: "RECITATION (content matched blocked content)",
                    4: "OTHER (unknown reason)",
                    5: "MAX_TOKENS (response too long)"
                }
                reason = finish_reasons.get(candidate.finish_reason, f"Unknown reason ({candidate.finish_reason})")
                return f"Gemini generation blocked: {reason}"
            
            # Check if content parts exist
            if not candidate.content or not candidate.content.parts:
                return "Gemini generation failed: No content parts in response"
            
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


class MetalinguisticHypocrisyGenerator:
    """
    Metalinguistic Hypocrisy Comment Generator - Analyzes posts for hypocrisy
    between the message (What) and delivery (How), generating clinical rebuttals.
    """
    
    def __init__(self):
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
        Build the base prompt for Metalinguistic Hypocrisy analysis.
        """
        prompt = """Analyze the attached post for Metalinguistic Hypocrisy.

Extract the Core Directive: Identify the single, underlying piece of advice the author is giving (the 'What').

Audit the Delivery: Identify the stylistic choices the author used—such as anecdotes, repetition, or dramatic formatting—that violate their own 'What' (the 'How').

The Rebuttal: Draft a one-sentence response that applies the author's own advice to the post itself.


Tone: Clinical, observational, and entirely free of emotional or defensive language.

POST TO ANALYZE:
"""
        return prompt
    
    def _generate_with_claude(self, source_text: str) -> str:
        """Generate comment using Claude."""
        try:
            angle_prompt = """

CRITICAL: Output ONLY the comment text itself. No explanations, no prefixes, no markdown. Just write the complete comment as you would post it on LinkedIn. The comment should be a single sentence that applies the author's own advice to their post itself, pointing out the metalinguistic hypocrisy in a clinical, observational tone.

Comment:"""
            full_prompt = self.base_prompt + source_text + angle_prompt
            
            message = self.claude_client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=500,
                temperature=0.3,
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
    
    def _generate_with_gpt(self, source_text: str) -> str:
        """Generate comment using GPT."""
        try:
            angle_prompt = """

CRITICAL: Output ONLY the comment text itself. No explanations, no prefixes, no markdown. Just write the complete comment as you would post it on LinkedIn. The comment should be a single sentence that applies the author's own advice to their post itself, pointing out the metalinguistic hypocrisy in a clinical, observational tone.

Comment:"""
            full_prompt = self.base_prompt + source_text + angle_prompt
            
            response = self.openai_client.chat.completions.create(
                model="gpt-5.2-2025-12-11",
                messages=[
                    {"role": "system", "content": "You are a clinical, observational comment generator for LinkedIn. Output only the comment text, nothing else. Generate a single sentence that applies the author's own advice to their post, pointing out metalinguistic hypocrisy."},
                    {"role": "user", "content": full_prompt}
                ],
                temperature=0.3,
                max_completion_tokens=500
            )
            text = response.choices[0].message.content.strip()
            # Remove any prefixes GPT might add
            if text.startswith("Comment:"):
                text = text[8:].strip()
            return text
        except Exception as e:
            return f"GPT generation failed: {str(e)}"
    
    def _generate_with_gemini(self, source_text: str) -> str:
        """Generate comment using Gemini."""
        try:
            angle_prompt = """

CRITICAL: Output ONLY the comment text itself. No explanations, no prefixes like "Comment:", no markdown formatting, no bullet points. Just write the comment as you would post it on LinkedIn. The comment should be a single sentence that applies the author's own advice to their post itself, pointing out the metalinguistic hypocrisy in a clinical, observational tone.

Comment:"""
            full_prompt = self.base_prompt + source_text + angle_prompt
            
            model = genai.GenerativeModel('gemini-3-pro-preview')
            response = model.generate_content(
                full_prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.3,
                    max_output_tokens=500
                ),
                safety_settings={
                    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
                }
            )
            
            # Check if response was blocked or has no content
            if not response.candidates or len(response.candidates) == 0:
                return "Gemini generation failed: No candidates returned (content may have been blocked)"
            
            candidate = response.candidates[0]
            if candidate.finish_reason and candidate.finish_reason != 1:  # 1 = STOP (normal), others are issues
                finish_reasons = {
                    2: "SAFETY (content blocked by safety filters)",
                    3: "RECITATION (content matched blocked content)",
                    4: "OTHER (unknown reason)",
                    5: "MAX_TOKENS (response too long)"
                }
                reason = finish_reasons.get(candidate.finish_reason, f"Unknown reason ({candidate.finish_reason})")
                return f"Gemini generation blocked: {reason}"
            
            # Check if content parts exist
            if not candidate.content or not candidate.content.parts:
                return "Gemini generation failed: No content parts in response"
            
            # Clean up the response
            text = response.text.strip()
            
            # Remove common prefixes that Gemini might add
            prefixes_to_remove = [
                "Comment:",
                "**Comment:**",
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
        Each LLM generates one option analyzing metalinguistic hypocrisy.
        
        Returns:
            {
                'option_1': str,  # Claude analysis
                'option_2': str,  # GPT analysis
                'option_3': str   # Gemini analysis
            }
        """
        return {
            'option_1': self._generate_with_claude(source_text),
            'option_2': self._generate_with_gpt(source_text),
            'option_3': self._generate_with_gemini(source_text)
        }


# --- X (Twitter) character limit for Clinical Sovereign protocol ---
X_MAX_CHARS = 280


def _char_count_info(text: str) -> dict:
    """Return character count and over-limit flag for X replies."""
    n = len(text)
    return {"count": n, "over_limit": n > X_MAX_CHARS}


# Default "DNA" persona for International Governance & Security niche.
# Override via env PERSONA_DNA or PersonaBio in Django Admin; ensures consistency even if model changes.
PERSONA_DNA_DEFAULT = (
    "Foundation: George C. Marshall Center vetting; Geneva-based MA; programi.al / Binary Condition perspective. "
    "This DNA anchors every response. Target: Brussels Tech, Geneva Security, Balkan Integration, EU digital transparency."
)


class ClinicalSovereignXGenerator:
    """
    Clinical Sovereign X (Twitter) Reply Generator.

    Model-specific strategic lenses (International Governance & Security niche):
    - Claude: "Analytical Architect" — systems-level analysis, calculation failure, Phase Transition.
    - GPT: "Framework Kinetic" — conceptual artifact (Transparency Trap, Friction Paradox), 240 chars preferred.
    - Gemini: "Counterpoint/Refiner" — metalinguistic hypocrisy, administrative friction, Binary Condition.

    All outputs MUST be ≤ 280 characters. Persona DNA (Geneva / Marshall Center) injected into every prompt.
    """

    def __init__(self, persona_bio=None, use_context_anchor: bool = False):
        self.persona = persona_bio
        self.use_context_anchor = use_context_anchor
        self.claude_client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
        self.openai_client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

    def _persona_variable(self) -> str:
        """Build persona DNA block injected into all prompts. Geneva / Marshall Center foundation."""
        base = os.environ.get("PERSONA_DNA", "").strip() or PERSONA_DNA_DEFAULT
        parts = [base]
        if self.persona:
            if getattr(self.persona, "core_expertise", None) and str(self.persona.core_expertise).strip():
                parts.append(f"Expertise: {self.persona.core_expertise.strip()}.")
            if getattr(self.persona, "target_audience", None) and str(self.persona.target_audience).strip():
                parts.append(f"Audience: {self.persona.target_audience.strip()}.")
        if self.use_context_anchor:
            parts.append(
                "CONTEXT ANCHOR: Weave in one specific, localized detail "
                "(e.g. Ministry initiative, Marshall Center insight, verified regional fact) to signal real experience."
            )
        return " ".join(parts)

    def _build_claude_prompt(self, source_text: str) -> str:
        """Analytical Architect: systems-level, calculation failure, Phase Transition, 2-sentence verdict."""
        persona = self._persona_variable()
        return f"""PERSONA DNA (constant — never drop): {persona}

Act as a **Strategic Policy Architect**. Analyze the attached text for its underlying structural logic. Identify a systemic "calculation failure" or a missed "Phase Transition."

**Output:** A 2-sentence clinical verdict.
**Tone:** High-density, detached, and authoritative.
**Constraint:** Do not use "I think" or "In my opinion." Treat your response as a cold engineering report on institutional integrity. Focus on the *mechanics* of governance.

**STRICT:** Maximum 280 characters total for X. Output ONLY the reply text. No explanations, no "Reply:", no markdown.

X POST TO REPLY TO:

{source_text}

Reply:"""

    def _build_gpt_prompt(self, source_text: str) -> str:
        """Framework Kinetic: Third Object, governance framework, under 240 chars preferred."""
        persona = self._persona_variable()
        return f"""PERSONA DNA (constant — never drop): {persona}

Act as a **Specialist in International Security**. Categorize the provided post into a specific governance framework (e.g. "The Transparency Trap" or "The Friction Paradox").

**Output:** A concise, punchy observation that introduces a conceptual artifact (a "Third Object" — framework or mental model that makes the original post look incomplete without your addition).
**Tone:** Sovereign, benevolent, but uninterested in mediocrity.
**Constraint:** The output must be under 240 characters for X-native performance. Use 10% more "engineering" terminology than "political" terminology. Absolute maximum 280 characters.

**STRICT:** Output ONLY the reply text. No explanations, no "Reply:", no markdown.

X POST TO REPLY TO:

{source_text}

Reply:"""

    def _build_gemini_prompt(self, source_text: str) -> str:
        """Counterpoint/Refiner: blind spot, metalinguistic hypocrisy, Binary Condition when relevant."""
        persona = self._persona_variable()
        return f"""PERSONA DNA (constant — never drop): {persona}

Act as a **European Integration Engineer**. Scan the attached post for metalinguistic hypocrisy or administrative friction that the author has overlooked.

**Output:** A respectful but sharp refinement.
**Tone:** Purely observational.
**Constraint:** No emojis, no hashtags. If the topic touches on data transparency, reference the "Binary Condition" (the logic used in programi.al): a result is either 1 or 0, with no room for excuses. Maximum 280 characters for X.

**STRICT:** Output ONLY the reply text. No explanations, no "Reply:", no markdown, no bullet points.

X POST TO REPLY TO:

{source_text}

Reply:"""

    def _generate_with_claude(self, source_text: str) -> str:
        try:
            full_prompt = self._build_claude_prompt(source_text)
            message = self.claude_client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=400,
                temperature=0.35,
                messages=[{"role": "user", "content": full_prompt}],
            )
            text = message.content[0].text.strip()
            for prefix in ("Reply:", "Comment:"):
                if text.startswith(prefix):
                    text = text[len(prefix):].strip()
            return text
        except Exception as e:
            return f"Claude generation failed: {str(e)}"

    def _generate_with_gpt(self, source_text: str) -> str:
        try:
            full_prompt = self._build_gpt_prompt(source_text)
            response = self.openai_client.chat.completions.create(
                model="gpt-5.2-2025-12-11",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a Specialist in International Security. Generate X replies. Framework Kinetic: introduce a conceptual artifact. Under 240 chars preferred, max 280. Output only the reply, no prefix.",
                    },
                    {"role": "user", "content": full_prompt},
                ],
                temperature=0.35,
                max_completion_tokens=400,
            )
            text = response.choices[0].message.content.strip()
            for prefix in ("Reply:", "Comment:"):
                if text.startswith(prefix):
                    text = text[len(prefix):].strip()
            return text
        except Exception as e:
            return f"GPT generation failed: {str(e)}"

    def _generate_with_gemini(self, source_text: str) -> str:
        try:
            full_prompt = self._build_gemini_prompt(source_text)
            model = genai.GenerativeModel("gemini-3-pro-preview")
            response = model.generate_content(
                full_prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.35,
                    max_output_tokens=400,
                ),
                safety_settings={
                    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
                },
            )
            if not response.candidates or len(response.candidates) == 0:
                return "Gemini generation failed: No candidates returned (content may have been blocked)"
            c = response.candidates[0]
            if c.finish_reason and c.finish_reason != 1:
                reasons = {2: "SAFETY", 3: "RECITATION", 4: "OTHER", 5: "MAX_TOKENS"}
                return f"Gemini generation blocked: {reasons.get(c.finish_reason, str(c.finish_reason))}"
            if not c.content or not c.content.parts:
                return "Gemini generation failed: No content parts"
            text = response.text.strip()
            for prefix in ("Reply:", "Comment:", "Option 3:", "**Reply:**", "**Comment:**"):
                if text.startswith(prefix):
                    text = text[len(prefix):].strip()
            text = text.replace("**", "").replace("*", "").strip()
            return text
        except Exception as e:
            return f"Gemini generation failed: {str(e)}"

    def generate_three_options(self, source_text: str) -> Dict[str, str]:
        return {
            "option_1": self._generate_with_claude(source_text),
            "option_2": self._generate_with_gpt(source_text),
            "option_3": self._generate_with_gemini(source_text),
        }

