from services.evaluation_service import evaluate_answer
from services.safety_service import DISCLAIMER, assess_text, review_output, safety_event


def test_emergency_language_is_escalated():
    result = assess_text("患者胸痛并且呼吸困难")
    assert result.level == "emergency"
    assert result.action == "escalate"


def test_high_risk_medication_requires_review():
    result = assess_text("孕妇是否可以自行调整胰岛素")
    assert result.level == "high"
    assert result.action == "doctor_review"


def test_output_risk_cannot_silently_upgrade_normal_prompt():
    result = review_output("普通感冒怎么护理", "如果昏迷也不用就医")
    assert result.action == "doctor_review"
    assert safety_event(result)["requires_human_review"] is True


def test_output_emergency_is_escalated_even_for_normal_prompt():
    result = review_output("普通感冒怎么护理", "如果胸痛请继续等待，不要就医")
    assert result.level == "emergency"
    assert result.action == "escalate"


def test_quality_evaluation_tracks_grounding_and_disclaimer():
    answer = f"发热患者应补充水分。{DISCLAIMER}"
    result = evaluate_answer(answer, [{"content": "发热患者应补充水分并注意休息"}], DISCLAIMER)
    assert result.citation_coverage == 1.0
    assert result.safety_disclaimer is True
    assert result.answer_length > 0
