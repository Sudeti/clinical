import json
from decimal import Decimal
from critique.analyzers import CritiqueAnalyzer


def test_parse_structured_and_consensus():
    # Prepare two mock LLM JSON outputs and one weak output
    j1 = json.dumps({
        "physics_engine_score": 80,
        "zero_kelvin_shield_score": 90,
        "verdict_output_score": 85,
        "scalpel_edge_score": 70,
        "kinetic_action_score": 40,
        "clinical_tone_score": 82,
        "venom_density": 60,
        "value_density": 70,
        "structural_failures": [],
        "artifact": "2x2 matrix: Effort vs Impact",
        "forbidden_alternatives": {"excited": ["pleased", "notable"]},
        "sentence_triggers": [1],
        "final_verdict": "CLEAR"
    })

    j2 = json.dumps({
        "physics_engine_score": 45,
        "verdict_output_score": 90,
        "clinical_tone_score": 60,
        "venom_density": 90,
        "value_density": 30,
        "final_verdict": "REVISE",
        "forbidden_alternatives": {"honored": ["grateful"]},
        "sentence_triggers": [2, 3],
        "artifact": "Checklist: 3 steps"
    })

    j3 = "Some error or non-json output"

    critiques = {"claude": j1, "gpt": j2, "gemini": j3}

    consensus = CritiqueAnalyzer.calculate_consensus(critiques)

    assert consensus['avg_clinical_score'] is not None
    assert consensus['artifact'] in ("2x2 matrix: Effort vs Impact", "Checklist: 3 steps")
    assert 'excited' in consensus['forbidden_alternatives']
    assert 1 in consensus['sentence_triggers']
    # Given mixed value density with multiple low-value signals, ensure decision not CLEAR
    assert consensus['consensus_verdict'] in ("REVISE", "REJECT")
