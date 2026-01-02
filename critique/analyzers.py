import re
from typing import Dict, Optional
from decimal import Decimal


class CritiqueAnalyzer:
    """
    Parse LLM critiques and extract structured data.
    """
    
    @staticmethod
    def extract_clinical_score(critique_text: str) -> Optional[int]:
        """
        Extract clinical tone score from LLM response.
        Looks for patterns like "Clinical Tone Score: 65" or "Score: 65/100"
        """
        patterns = [
            r'clinical\s+tone\s+score[:\s]+(\d+)',
            r'tone\s+score[:\s]+(\d+)',
            r'score[:\s]+(\d+)(?:/100)?',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, critique_text, re.IGNORECASE)
            if match:
                score = int(match.group(1))
                # Ensure score is 0-100
                if 0 <= score <= 100:
                    return score
        
        return None
    
    @staticmethod
    def extract_verdict(critique_text: str) -> Optional[str]:
        """
        Extract final verdict from LLM response.
        Looks for CLEAR, REVISE, or REJECT keywords.
        """
        text_upper = critique_text.upper()
        
        # Check for explicit verdict statements
        if 'VERDICT:' in text_upper or 'FINAL VERDICT:' in text_upper:
            if 'CLEAR' in text_upper:
                return 'CLEAR'
            elif 'REJECT' in text_upper:
                return 'REJECT'
            elif 'REVISE' in text_upper:
                return 'REVISE'
        
        # Fallback: Count severity indicators
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
    def calculate_consensus(critiques: Dict[str, str]) -> Dict:
        """
        Analyze all three critiques and generate consensus metrics.
        
        Returns:
            {
                'avg_clinical_score': Decimal or None,
                'consensus_verdict': str ('CLEAR', 'REVISE', 'REJECT')
            }
        """
        scores = []
        verdicts = []
        
        # Extract from each LLM
        for llm_name, critique_text in critiques.items():
            if not critique_text or 'failed' in critique_text.lower():
                continue
            
            # Extract clinical score
            score = CritiqueAnalyzer.extract_clinical_score(critique_text)
            if score is not None:
                scores.append(score)
            
            # Extract verdict
            verdict = CritiqueAnalyzer.extract_verdict(critique_text)
            if verdict:
                verdicts.append(verdict)
        
        # Calculate average clinical score
        avg_score = None
        if scores:
            avg_score = Decimal(sum(scores) / len(scores)).quantize(Decimal('0.1'))
        
        # Determine consensus verdict
        consensus_verdict = 'REVISE'  # Default
        
        if verdicts:
            # If any LLM says REJECT, consensus is REJECT
            if 'REJECT' in verdicts:
                consensus_verdict = 'REJECT'
            # If all say CLEAR, consensus is CLEAR
            elif all(v == 'CLEAR' for v in verdicts):
                consensus_verdict = 'CLEAR'
            # If majority say CLEAR (2 out of 3), consensus is CLEAR
            elif verdicts.count('CLEAR') >= 2:
                consensus_verdict = 'CLEAR'
            # Otherwise, REVISE
        
        return {
            'avg_clinical_score': avg_score,
            'consensus_verdict': consensus_verdict
        }