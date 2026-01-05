import re
import json
from typing import Dict, Optional, Any
from decimal import Decimal


class CritiqueAnalyzer:
    """
    Parse LLM critiques and extract structured data. Prefer JSON mode outputs
    and fall back to earlier regex heuristics only when necessary.
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
    def extract_clinical_score(critique_text: str) -> Optional[int]:
        """
        Prefer extracting 'clinical_tone_score' from JSON. Fallback to regex.
        """
        # Try JSON first
        parsed = CritiqueAnalyzer._parse_json_block(critique_text)
        if parsed and 'clinical_tone_score' in parsed:
            try:
                sc = int(parsed['clinical_tone_score'])
                if 0 <= sc <= 100:
                    return sc
            except Exception:
                pass

        # Regex fallback (legacy support)
        patterns = [
            r'clinical\s+tone\s+score[:\s]+(\d+)',
            r'tone\s+score[:\s]+(\d+)',
            r'score[:\s]+(\d+)(?:/100)?',
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
        Prefer 'final_verdict' from JSON. Fallback to heuristics.
        """
        parsed = CritiqueAnalyzer._parse_json_block(critique_text)
        if parsed and 'final_verdict' in parsed:
            v = parsed['final_verdict'].upper()
            if v in ('CLEAR', 'REVISE', 'REJECT'):
                return v

        # Old heuristic fallback
        text_upper = critique_text.upper()
        if 'VERDICT:' in text_upper or 'FINAL VERDICT:' in text_upper:
            if 'CLEAR' in text_upper:
                return 'CLEAR'
            elif 'REJECT' in text_upper:
                return 'REJECT'
            elif 'REVISE' in text_upper:
                return 'REVISE'

        reject_indicators = ['reject', 'fail', 'unacceptable', 'do not publish']
        clear_indicators = ['clear', 'publish', 'approved', 'ready']

        reject_count = sum(1 for term in reject_indicators if term in text_upper)
        clear_count = sum(1 for term in clear_indicators if term in text_upper)

        if reject_count > clear_count and reject_count > 2:
            return 'REJECT'
        elif clear_count > reject_count and clear_count > 2:
            return 'CLEAR'
        else:
            return 'REVISE'

    @staticmethod
    def parse_structured(critique_text: str) -> Dict[str, Any]:
        """
        Parse the critique text into a structured dict with expected keys.

        Returns a dict with defaults when keys are missing. Keys:
        - physics_engine_score, zero_kelvin_shield_score, verdict_output_score,
          scalpel_edge_score, kinetic_action_score, clinical_tone_score,
          venom_density, value_density, structural_failures (list), artifact (str),
          forbidden_alternatives (dict), sentence_triggers (list), final_verdict (str), notes
        """
        parsed = CritiqueAnalyzer._parse_json_block(critique_text) or {}

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

        return {
            'physics_engine_score': as_int('physics_engine_score'),
            'zero_kelvin_shield_score': as_int('zero_kelvin_shield_score'),
            'verdict_output_score': as_int('verdict_output_score'),
            'scalpel_edge_score': as_int('scalpel_edge_score'),
            'kinetic_action_score': as_int('kinetic_action_score'),
            'clinical_tone_score': as_int('clinical_tone_score'),
            'venom_density': as_int('venom_density'),
            'value_density': as_int('value_density'),
            'structural_failures': as_list('structural_failures'),
            'artifact': parsed.get('artifact', ''),
            'forbidden_alternatives': as_dict('forbidden_alternatives'),
            'sentence_triggers': as_list('sentence_triggers'),
            'final_verdict': (parsed.get('final_verdict') or '').upper(),
            'notes': parsed.get('notes', '')
        }

    @staticmethod
    def calculate_consensus(critiques: Dict[str, str]) -> Dict:
        """
        Analyze all three critiques and generate consensus metrics. Now accounts for
        'venom' vs 'value' balancing: venomous tone is acceptable but low argument
        density (low 'value_density') is a failure even if the Weapon is strong.

        Returns a dict with:
            avg_clinical_score (Decimal or None),
            consensus_verdict (CLEAR/REVISE/REJECT),
            artifact (chosen artifact or empty),
            forbidden_alternatives (merged mapping),
            sentence_triggers (merged list)
        """
        scores = []
        parsed_list = []

        for llm_name, critique_text in critiques.items():
            if not critique_text or 'failed' in critique_text.lower():
                continue
            parsed = CritiqueAnalyzer.parse_structured(critique_text)
            parsed_list.append(parsed)
            if parsed['clinical_tone_score'] is not None:
                scores.append(parsed['clinical_tone_score'])

        # Average clinical score
        avg_score = None
        if scores:
            avg_score = Decimal(sum(scores) / len(scores)).quantize(Decimal('0.1'))

        # Combine verdicts and inspect for engine failures
        final_verdicts = [p['final_verdict'] for p in parsed_list if p.get('final_verdict')]

        # If any LLM explicitly rejects -> REJECT
        if 'REJECT' in final_verdicts:
            consensus = 'REJECT'
        else:
            # Evaluate venom vs value failures
            low_value_alerts = 0
            strong_weapon_but_weak_engine = 0
            for p in parsed_list:
                v_density = p.get('value_density') or 0
                venom = p.get('venom_density') or 0
                weapon = p.get('verdict_output_score') or 0
                engine = p.get('physics_engine_score') or 0

                if v_density < 40 and (weapon > 70):
                    # Venom without substance
                    strong_weapon_but_weak_engine += 1
                if v_density < 30 and engine < 40:
                    low_value_alerts += 1

            # Decide consensus
            if strong_weapon_but_weak_engine >= 2 or low_value_alerts >= 2:
                consensus = 'REJECT'
            elif final_verdicts.count('CLEAR') >= 2:
                consensus = 'CLEAR'
            elif len(final_verdicts) > 0:
                consensus = 'REVISE'
            else:
                consensus = 'REVISE'

        # Pick artifact from the first parser that provides one
        artifact = ''
        for p in parsed_list:
            if p.get('artifact'):
                artifact = p.get('artifact')
                break

        # Merge forbidden alternatives (LLM outputs are dicts)
        merged_alts = {}
        for p in parsed_list:
            for k, v in p.get('forbidden_alternatives', {}).items():
                merged_alts.setdefault(k, []).extend(v if isinstance(v, list) else [v])

        # Deduplicate merged alternatives
        for k in list(merged_alts.keys()):
            merged_alts[k] = list(dict.fromkeys(merged_alts[k]))

        # Merge sentence triggers (unique, sorted)
        triggers = set()
        for p in parsed_list:
            for idx in p.get('sentence_triggers', []) or []:
                try:
                    triggers.add(int(idx))
                except Exception:
                    pass
        sentence_triggers = sorted(list(triggers))

        return {
            'avg_clinical_score': avg_score,
            'consensus_verdict': consensus,
            'artifact': artifact,
            'forbidden_alternatives': merged_alts,
            'sentence_triggers': sentence_triggers
        }