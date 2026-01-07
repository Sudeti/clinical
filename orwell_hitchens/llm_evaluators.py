import os
import anthropic
import openai
import google.generativeai as genai
from typing import Dict

ORWELL_HITCHENS_SYSTEM_MESSAGE = """
You are a writing critic trained on Orwell's "Politics and the English Language" 
and Hitchens's rhetorical precision.

Core Principles:
- Never let a metaphor die of mixed company
- Concrete nouns defeat abstract fog
- Active voice carries conviction
- Every sentence must justify its existence
- Wit sharpens argument; it doesn't replace it

Your task: Dissect the draft with surgical precision. Attack weak verbs, 
murky logic, lazy metaphors, and bureaucratic evasions.

Metaphor Constraint: Evaluate how images work (or fail) in the text—don't 
assess literal physics unless the text itself discusses physics.

Be ruthless but constructive. Point to specific failures and suggest concrete improvements.
"""


class OrwellHitchensEngine:
    """
    Multi-LLM evaluation system for Orwellian clarity and Hitchensian fire.
    """
    
    def __init__(self, writer_profile, published_pieces):
        self.profile = writer_profile
        self.published_pieces = published_pieces
        
        # Initialize API clients
        self.claude_client = anthropic.Anthropic(
            api_key=os.environ.get("ANTHROPIC_API_KEY")
        )
        openai.api_key = os.environ.get("OPENAI_API_KEY")
        genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
        
        self.evaluation_prompt = self._build_evaluation_prompt()
    
    def _build_evaluation_prompt(self) -> str:
        """
        Construct the Orwell-Hitchens evaluation prompt.
        """
        past_pieces_sample = "\n\n".join([
            f"PAST PIECE ({piece.published_date}) - {piece.publication}:\n{piece.content[:600]}..."
            for piece in self.published_pieces[:3]
        ])
        
        prompt = f"""You are evaluating writing for a {self.profile.professional_context} using the ORWELL-HITCHENS framework.

THE ORWELL-HITCHENS FRAMEWORK:

I. ORWELLIAN CLARITY (40% Weight)
   - Concrete vs. Abstract: Count and flag abstract nouns (situation, aspect, factor, context, framework)
   - Active Voice Ratio: Passive voice weakens impact. Flag all passive constructions.
   - Sentence Length Variance: Mix short punches with longer flows. Monotony kills rhythm.
   - Jargon Density: Flag bureaucratic euphemisms and business-speak
   - Word Choice: Prefer Anglo-Saxon roots over Latinate abstractions
   
   Orwell's Rule: "Never use a long word where a short one will do."

II. HITCHENSIAN FIRE (30% Weight)
   - Argument Structure: Does each paragraph advance a clear claim?
   - Logical Scaffolding: Are premises explicitly connected to conclusions?
   - Rhetorical Devices: Identify effective use of:
     * Parallelism (repeating structure for emphasis)
     * Antithesis (contrasting ideas in balanced phrases)
     * Tricolon (three-part lists for rhythm)
   - Wit Density: Unexpected comparisons, precision insults, elegant reversals
   - Intellectual Honesty: Does it address counterarguments or strawman?
   
   Hitchens's Rule: "What can be asserted without evidence can be dismissed without evidence."

III. VIVID PHYSICALITY (20% Weight)
   - Sensory Language Ratio: How much appeals to sight, sound, texture, smell, taste?
   - Metaphor Coherence: Flag mixed metaphors mercilessly
   - Concrete Imagery vs. Vague Generalities: "Show don't tell" violations
   - Physical Grounding: Abstract ideas anchored in physical reality
   
   Combined Rule: Make abstractions visible, tangible, smellable.

IV. TECHNICAL EXECUTION (10% Weight)
   - Grammar Errors: Identify and correct
   - Redundancies: Flag filler words (very, really, actually, basically)
   - Cliché Detection: Mark tired phrases and suggest fresh alternatives
   - Flow Disruptions: Awkward transitions, logical gaps
   
FORBIDDEN JARGON (Writer's Personal List):
{self.profile.forbidden_jargon}

WRITER'S STYLE PREFERENCES:
{self.profile.style_preferences}

CALIBRATION DATA (Writer's Past High-Performing Work):
{past_pieces_sample if past_pieces_sample.strip() else "No published pieces available for calibration."}

---

YOUR ROLE: WRITING COACH

You're not grading a paper. You're coaching a writer who wants to improve their craft.

Read their draft through the Orwell-Hitchens lens:
- Does it use concrete language or hide behind abstractions?
- Does it make arguments or just state opinions?
- Can you see/smell/feel what they're describing?
- Is it technically clean?

Then write them a coaching letter. Be honest, specific, and useful.

**START WITH SCORES** (just list them naturally):
```
Orwellian Clarity: X/100
Hitchensian Fire: X/100
Vivid Physicality: X/100
Technical Execution: X/100
Verdict: PUBLISH | REVISE | REWRITE
```

**THEN COACH THEM**:

1. **What's working?** (Be specific - quote what they did well)
   
2. **What's the core problem?** (Pick 1-2 main issues, not a laundry list)
   - Quote the weakest passages
   - Show how to rewrite them
   - Explain WHY your version works better
   
3. **What patterns do you notice?** (Habits they keep repeating)
   
4. **What should they do in their next draft?** (3 concrete actions, not vague advice)

Write naturally. No bullet points required. No JSON. Just talk to them like a mentor.

Be ruthless about weakness but encouraging about potential. The goal is improvement, not destruction.

Be specific. Be brutal. Be constructive. Most importantly: Be useful.

---

DRAFT TO EVALUATE:

"""
        return prompt
    
    def evaluate_with_claude(self, draft_text: str) -> str:
        """Claude Orwell-Hitchens evaluation."""
        try:
            full_prompt = (
                ORWELL_HITCHENS_SYSTEM_MESSAGE.strip()
                + "\n\n"
                + self.evaluation_prompt
                + draft_text
            )

            message = self.claude_client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=3000,
                temperature=0.2,
                messages=[
                    {
                        "role": "user",
                        "content": full_prompt
                    }
                ]
            )

            return message.content[0].text

        except Exception as e:
            return f"Claude evaluation failed: {str(e)}"
    
    def evaluate_with_gpt(self, draft_text: str) -> str:
        """GPT Orwell-Hitchens evaluation."""
        try:
            client = openai.OpenAI()
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": ORWELL_HITCHENS_SYSTEM_MESSAGE
                    },
                    {
                        "role": "user",
                        "content": self.evaluation_prompt + draft_text
                    }
                ],
                temperature=0.2,
                max_completion_tokens=3000
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"GPT evaluation failed: {str(e)}"
    
    def evaluate_with_gemini(self, draft_text: str) -> str:
        """Gemini Orwell-Hitchens evaluation."""
        try:
            model = genai.GenerativeModel("gemini-2.0-flash-exp")

            full_prompt = (
                ORWELL_HITCHENS_SYSTEM_MESSAGE.strip()
                + "\n\n"
                + self.evaluation_prompt
                + draft_text
            )

            response = model.generate_content(
                full_prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.2,
                    max_output_tokens=3000
                )
            )
            return response.text
        except Exception as e:
            return f"Gemini evaluation failed: {str(e)}"
    
    def execute_full_evaluation(self, draft_text: str) -> Dict[str, str]:
        """Run all three evaluations in parallel."""
        return {
            'claude': self.evaluate_with_claude(draft_text),
            'gpt': self.evaluate_with_gpt(draft_text),
            'gemini': self.evaluate_with_gemini(draft_text)
        }

