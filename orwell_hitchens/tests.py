from django.test import TestCase
from django.contrib.auth.models import User
from .models import WriterProfile, PublishedPiece, DraftEvaluation
from .analyzers import WritingAnalyzer


class WritingAnalyzerTestCase(TestCase):
    """Test the WritingAnalyzer consensus logic."""

    def test_parse_json_block(self):
        """Test JSON extraction from LLM responses."""
        critique_text = """
        Here's my evaluation:
        {
            "orwellian_clarity_score": 75,
            "hitchensian_fire_score": 80,
            "verdict": "REVISE"
        }
        """
        parsed = WritingAnalyzer._parse_json_block(critique_text)
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed['orwellian_clarity_score'], 75)
        self.assertEqual(parsed['verdict'], 'REVISE')

    def test_extract_verdict(self):
        """Test verdict extraction."""
        critique_with_publish = '{"verdict": "PUBLISH"}'
        verdict = WritingAnalyzer.extract_verdict(critique_with_publish)
        self.assertEqual(verdict, 'PUBLISH')

    def test_calculate_consensus(self):
        """Test consensus calculation across multiple LLMs."""
        critiques = {
            'claude': '{"orwellian_clarity_score": 70, "hitchensian_fire_score": 75, "vivid_physicality_score": 65, "technical_execution_score": 80, "verdict": "REVISE"}',
            'gpt': '{"orwellian_clarity_score": 72, "hitchensian_fire_score": 78, "vivid_physicality_score": 68, "technical_execution_score": 82, "verdict": "REVISE"}',
            'gemini': '{"orwellian_clarity_score": 68, "hitchensian_fire_score": 73, "vivid_physicality_score": 62, "technical_execution_score": 78, "verdict": "PUBLISH"}',
        }
        
        consensus = WritingAnalyzer.calculate_consensus(critiques)
        
        self.assertIsNotNone(consensus['orwellian_clarity_score'])
        self.assertIsNotNone(consensus['overall_score'])
        self.assertIn(consensus['consensus_verdict'], ['PUBLISH', 'REVISE', 'REWRITE'])


class WriterProfileTestCase(TestCase):
    """Test WriterProfile model."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testwriter',
            password='testpass123'
        )

    def test_create_writer_profile(self):
        """Test creating a writer profile."""
        profile = WriterProfile.objects.create(
            user=self.user,
            professional_context='Political Analyst',
            writing_domains='Foreign policy, international relations',
            forbidden_jargon='synergy, leverage, robust'
        )
        
        self.assertEqual(profile.user, self.user)
        self.assertIn('synergy', profile.forbidden_jargon)


class DraftEvaluationTestCase(TestCase):
    """Test DraftEvaluation model."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testwriter',
            password='testpass123'
        )

    def test_create_draft_evaluation(self):
        """Test creating a draft evaluation."""
        evaluation = DraftEvaluation.objects.create(
            user=self.user,
            draft_text='This is a test draft for evaluation.',
            consensus_verdict='PROCESSING'
        )
        
        self.assertEqual(evaluation.user, self.user)
        self.assertEqual(evaluation.consensus_verdict, 'PROCESSING')
        self.assertIsNone(evaluation.overall_score)


class ViewsTestCase(TestCase):
    """Test views (requires login)."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testwriter',
            password='testpass123'
        )
        self.client.login(username='testwriter', password='testpass123')

    def test_evaluate_draft_view_get(self):
        """Test GET request to evaluate_draft view."""
        response = self.client.get('/orwell/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'ORWELL-HITCHENS WRITING ENGINE')

    def test_evaluate_draft_view_post(self):
        """Test POST request to submit a draft."""
        draft_text = 'This is a test draft that is longer than one hundred characters to meet the minimum requirement for submission to the evaluation engine.'
        response = self.client.post('/orwell/', {'draft_text': draft_text})
        
        # Should redirect after successful submission
        self.assertEqual(response.status_code, 302)
        
        # Should create a DraftEvaluation record
        self.assertTrue(DraftEvaluation.objects.filter(user=self.user).exists())

    def test_evaluation_history_view(self):
        """Test evaluation history view."""
        response = self.client.get('/orwell/history/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'EVALUATION HISTORY')
