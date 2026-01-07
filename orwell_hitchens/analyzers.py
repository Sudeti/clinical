import re
import json
from typing import Dict, Optional, Any, List
from decimal import Decimal


class WritingAnalyzer:
    """
    Parse LLM evaluations and extract structured data for the Orwell-Hitchens framework.
    """

    @staticmethod
    def _parse_json_block(text: str) -> Optional[Dict[str, Any]]:
        """Try to extract a JSON object from the freeform text and parse it."""
        if not text or '{' not in text:
            return None
        try:
            # If the entire response is JSON, json.loads works directly
            parsed = json.loads(text)
            if isinstance(parsed, dict):
                return parsed
        except Exception:
            pass

        # Fallback: try to find the first JSON object substring
        try:
            start = text.index('{')
            end = text.rindex('}') + 1
            substr = text[start:end]
            parsed = json.loads(substr)
            if isinstance(parsed, dict):
                return parsed
        except Exception:
            return None

        return None

    @staticmethod
    def extract_score(critique_text: str, score_key: str) -> Optional[int]:
        """
        Extract a specific score from JSON or fallback to regex.
        """
        # Try JSON first
        parsed = WritingAnalyzer._parse_json_block(critique_text)
        if parsed and score_key in parsed:
            try:
                sc = int(parsed[score_key])
                if 0 <= sc <= 100:
                    return sc
            except Exception:
                pass

        # Regex fallback (legacy support)
        # Convert score_key to human-readable pattern
        pattern_name = score_key.replace('_', r'\s+')
        patterns = [
            rf'{pattern_name}[:\s]+(\d+)',
            rf'score[:\s]+(\d+)(?:/100)?',
        ]

        for pattern in patterns:
            match = re.search(pattern, critique_text, re.IGNORECASE)
            if match:
                score = int(match.group(1))
                if 0 <= score <= 100:
                    return score

        return None

    @staticmethod
    def extract_verdict(critique_text: str) -> Optional[str]:
        """
        Extract verdict from JSON or heuristics.
        """
        parsed = WritingAnalyzer._parse_json_block(critique_text)
        if parsed and 'verdict' in parsed:
            v = parsed['verdict'].upper()
            if v in ('PUBLISH', 'REVISE', 'REWRITE'):
                return v

        # Old heuristic fallback
        text_upper = critique_text.upper()
        if 'VERDICT:' in text_upper:
            if 'PUBLISH' in text_upper:
                return 'PUBLISH'
            elif 'REWRITE' in text_upper:
                return 'REWRITE'
            elif 'REVISE' in text_upper:
                return 'REVISE'

        # Count indicators
        publish_indicators = ['publish', 'ready', 'strong', 'clear', 'excellent']
        rewrite_indicators = ['rewrite', 'fail', 'weak', 'unclear', 'confusing']
        
        publish_count = sum(1 for term in publish_indicators if term in text_upper)
        rewrite_count = sum(1 for term in rewrite_indicators if term in text_upper)

        if rewrite_count > publish_count and rewrite_count > 2:
            return 'REWRITE'
        elif publish_count > rewrite_count and publish_count > 2:
            return 'PUBLISH'
        else:
            return 'REVISE'

    @staticmethod
    def parse_structured(critique_text: str) -> Dict[str, Any]:
        """
        Parse the critique text into a structured dict.

        Returns a dict with defaults when keys are missing. Keys:
        - orwellian_clarity_score, hitchensian_fire_score, vivid_physicality_score,
          technical_execution_score, abstract_nouns (list), passive_voice_sentences (list),
          jargon_violations (dict), weak_verbs (list), rhetorical_highlights (list),
          verdict (str), summary (str)
        - NEW COACHING FIELDS: diagnostic_summary, before_after_examples, strengths_to_amplify,
          recurring_patterns, concrete_next_steps, one_sentence_verdict
        """
        parsed = WritingAnalyzer._parse_json_block(critique_text) or {}

        # Normalize and provide safe defaults
        def as_int(k, default=None):
            try:
                v = parsed.get(k, default)
                return int(v) if v is not None else default
            except Exception:
                return default

        def as_list(k):
            v = parsed.get(k)
            return v if isinstance(v, list) else []

        def as_dict(k):
            v = parsed.get(k)
            return v if isinstance(v, dict) else {}
        
        def as_str(k, default=''):
            v = parsed.get(k, default)
            return str(v) if v is not None else default

        return {
            'orwellian_clarity_score': as_int('orwellian_clarity_score'),
            'hitchensian_fire_score': as_int('hitchensian_fire_score'),
            'vivid_physicality_score': as_int('vivid_physicality_score'),
            'technical_execution_score': as_int('technical_execution_score'),
            'abstract_nouns': as_list('abstract_nouns'),
            'passive_voice_sentences': as_list('passive_voice_sentences'),
            'jargon_violations': as_dict('jargon_violations'),
            'weak_verbs': as_list('weak_verbs'),
            'rhetorical_highlights': as_list('rhetorical_highlights'),
            'verdict': (parsed.get('verdict') or '').upper(),
            'summary': parsed.get('summary', ''),
            # Coaching fields
            'diagnostic_summary': as_str('diagnostic_summary'),
            'before_after_examples': as_list('before_after_examples'),
            'strengths_to_amplify': as_list('strengths_to_amplify'),
            'recurring_patterns': as_list('recurring_patterns'),
            'concrete_next_steps': as_list('concrete_next_steps'),
            'one_sentence_verdict': as_str('one_sentence_verdict')
        }

    @staticmethod
    def calculate_consensus(critiques: Dict[str, str]) -> Dict:
        """
        Analyze all three critiques and generate consensus metrics.

        Returns a dict with:
            orwellian_clarity_score (Decimal or None),
            hitchensian_fire_score (Decimal or None),
            vivid_physicality_score (Decimal or None),
            technical_execution_score (Decimal or None),
            overall_score (Decimal or None, weighted average),
            consensus_verdict (PUBLISH/REVISE/REWRITE),
            abstract_nouns (merged list),
            passive_voice_sentences (merged list),
            jargon_violations (merged dict),
            weak_verbs (merged list),
            rhetorical_highlights (merged list)
        """
        clarity_scores = []
        fire_scores = []
        physicality_scores = []
        technical_scores = []
        parsed_list = []

        for llm_name, critique_text in critiques.items():
            if not critique_text or 'failed' in critique_text.lower():
                continue
            parsed = WritingAnalyzer.parse_structured(critique_text)
            parsed_list.append(parsed)
            
            if parsed['orwellian_clarity_score'] is not None:
                clarity_scores.append(parsed['orwellian_clarity_score'])
            if parsed['hitchensian_fire_score'] is not None:
                fire_scores.append(parsed['hitchensian_fire_score'])
            if parsed['vivid_physicality_score'] is not None:
                physicality_scores.append(parsed['vivid_physicality_score'])
            if parsed['technical_execution_score'] is not None:
                technical_scores.append(parsed['technical_execution_score'])

        # Average scores
        avg_clarity = None
        if clarity_scores:
            avg_clarity = Decimal(sum(clarity_scores) / len(clarity_scores)).quantize(Decimal('0.1'))
        
        avg_fire = None
        if fire_scores:
            avg_fire = Decimal(sum(fire_scores) / len(fire_scores)).quantize(Decimal('0.1'))
        
        avg_physicality = None
        if physicality_scores:
            avg_physicality = Decimal(sum(physicality_scores) / len(physicality_scores)).quantize(Decimal('0.1'))
        
        avg_technical = None
        if technical_scores:
            avg_technical = Decimal(sum(technical_scores) / len(technical_scores)).quantize(Decimal('0.1'))

        # Calculate weighted overall score
        # Weights: Clarity 40%, Fire 30%, Physicality 20%, Technical 10%
        overall_score = None
        if avg_clarity and avg_fire and avg_physicality and avg_technical:
            weighted = (
                float(avg_clarity) * 0.40 +
                float(avg_fire) * 0.30 +
                float(avg_physicality) * 0.20 +
                float(avg_technical) * 0.10
            )
            overall_score = Decimal(weighted).quantize(Decimal('0.1'))

        # Combine verdicts
        final_verdicts = [p['verdict'] for p in parsed_list if p.get('verdict')]

        # If any LLM says REWRITE -> REWRITE
        if 'REWRITE' in final_verdicts:
            consensus = 'REWRITE'
        elif final_verdicts.count('PUBLISH') >= 2:
            consensus = 'PUBLISH'
        elif len(final_verdicts) > 0:
            consensus = 'REVISE'
        else:
            consensus = 'REVISE'

        # Merge abstract nouns (unique)
        abstract_nouns = set()
        for p in parsed_list:
            for noun in p.get('abstract_nouns', []) or []:
                abstract_nouns.add(str(noun).lower())
        
        # Merge passive voice sentences (unique, sorted)
        passive_sentences = set()
        for p in parsed_list:
            for idx in p.get('passive_voice_sentences', []) or []:
                try:
                    passive_sentences.add(int(idx))
                except Exception:
                    pass

        # Merge jargon violations
        merged_jargon = {}
        for p in parsed_list:
            for term, alternatives in p.get('jargon_violations', {}).items():
                merged_jargon.setdefault(term, []).extend(
                    alternatives if isinstance(alternatives, list) else [alternatives]
                )
        
        # Deduplicate jargon alternatives
        for term in list(merged_jargon.keys()):
            merged_jargon[term] = list(dict.fromkeys(merged_jargon[term]))

        # Merge weak verbs (unique)
        weak_verbs = set()
        for p in parsed_list:
            for verb in p.get('weak_verbs', []) or []:
                weak_verbs.add(str(verb).lower())

        # Merge rhetorical highlights
        rhetorical_highlights = []
        for p in parsed_list:
            rhetorical_highlights.extend(p.get('rhetorical_highlights', []) or [])

        # Merge coaching fields
        diagnostic_summaries = [p.get('diagnostic_summary', '') for p in parsed_list if p.get('diagnostic_summary')]
        best_diagnostic = diagnostic_summaries[0] if diagnostic_summaries else ''
        
        # Collect all before/after examples (limit to best 5)
        all_before_after = []
        for p in parsed_list:
            all_before_after.extend(p.get('before_after_examples', []) or [])
        before_after_examples = all_before_after[:5]  # Top 5 examples
        
        # Merge strengths
        strengths_to_amplify = []
        for p in parsed_list:
            strengths_to_amplify.extend(p.get('strengths_to_amplify', []) or [])
        
        # Merge patterns (unique)
        recurring_patterns_set = set()
        for p in parsed_list:
            for pattern in p.get('recurring_patterns', []) or []:
                recurring_patterns_set.add(str(pattern))
        recurring_patterns = list(recurring_patterns_set)
        
        # Merge next steps (unique, limit to best 5)
        next_steps_set = []
        for p in parsed_list:
            for step in p.get('concrete_next_steps', []) or []:
                if step not in next_steps_set:
                    next_steps_set.append(step)
        concrete_next_steps = next_steps_set[:5]
        
        # Best one-sentence verdict
        one_sentence_verdicts = [p.get('one_sentence_verdict', '') for p in parsed_list if p.get('one_sentence_verdict')]
        one_sentence_verdict = one_sentence_verdicts[0] if one_sentence_verdicts else ''

        return {
            'orwellian_clarity_score': avg_clarity,
            'hitchensian_fire_score': avg_fire,
            'vivid_physicality_score': avg_physicality,
            'technical_execution_score': avg_technical,
            'overall_score': overall_score,
            'consensus_verdict': consensus,
            'abstract_nouns': sorted(list(abstract_nouns)),
            'passive_voice_sentences': sorted(list(passive_sentences)),
            'jargon_violations': merged_jargon,
            'weak_verbs': sorted(list(weak_verbs)),
            'rhetorical_highlights': rhetorical_highlights,
            # Coaching fields
            'diagnostic_summary': best_diagnostic,
            'before_after_examples': before_after_examples,
            'strengths_to_amplify': strengths_to_amplify,
            'recurring_patterns': recurring_patterns,
            'concrete_next_steps': concrete_next_steps,
            'one_sentence_verdict': one_sentence_verdict
        }

    @staticmethod
    def highlight_sentences(draft_text: str, sentence_indices: List[int]) -> str:
        """
        Highlight specific sentences in the draft text (for passive voice, etc).
        Returns HTML with <mark> tags.
        """
        if not sentence_indices:
            return draft_text
        
        # Simple sentence splitting (doesn't handle edge cases perfectly)
        sentences = re.split(r'(?<=[.!?])\s+', draft_text)
        
        highlighted = []
        for i, sentence in enumerate(sentences):
            if i in sentence_indices:
                highlighted.append(f'<mark class="bg-yellow-900 text-white">{sentence}</mark>')
            else:
                highlighted.append(sentence)
        
        return ' '.join(highlighted)

