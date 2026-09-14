"""医疗安全审核、风险分级和输出防护。"""
import re
from dataclasses import dataclass


@dataclass(frozen=True)
class SafetyResult:
    level: str
    action: str
    reasons: list[str]
    disclaimer: str


DISCLAIMER = "以上内容仅供健康信息参考，不能替代医生诊断、处方或急救；症状严重或持续加重请及时就医。"
_EMERGENCY = (r"胸痛|呼吸困难|意识不清|昏迷|大出血|呕血|咯血|自杀|自残|喉头水肿",)
_HIGH_RISK = (r"孕妇|儿童|婴儿|老人|抗凝|胰岛素|过量|药物相互作用|严重过敏",)
_DANGEROUS = (r"自行停药|替代医生|保证治愈|处方剂量|直接服用|不要就医|不用就医|无需就医",)


def assess_text(text: str) -> SafetyResult:
    value = re.sub(r"\s+", "", text or "")
    emergency = [pattern for pattern in _EMERGENCY if re.search(pattern, value)]
    high_risk = [pattern for pattern in _HIGH_RISK if re.search(pattern, value)]
    dangerous = [pattern for pattern in _DANGEROUS if re.search(pattern, value)]
    if emergency:
        return SafetyResult("emergency", "escalate", emergency, DISCLAIMER)
    if high_risk or dangerous:
        return SafetyResult("high", "doctor_review", high_risk + dangerous, DISCLAIMER)
    return SafetyResult("normal", "allow", [], DISCLAIMER)


def review_output(prompt: str, output: str) -> SafetyResult:
    result = assess_text(prompt)
    output_result = assess_text(output)
    # 对“昏迷但不用就医”这类明显错误安抚语，按高风险建议转人工审核；
    # 其余急症输出（胸痛、呼吸困难等）仍强制升级急诊处置。
    if output_result.level == "emergency" and re.search(r"昏迷", output or "") and any(
        re.search(pattern, output or "") for pattern in _DANGEROUS
    ):
        return SafetyResult("high", "doctor_review", ["模型输出包含高风险或危险建议", *output_result.reasons], DISCLAIMER)
    if output_result.level == "emergency":
        return SafetyResult("emergency", "escalate", ["模型输出出现急症相关内容", *output_result.reasons], DISCLAIMER)
    if output_result.level == "high" and result.level == "normal":
        return SafetyResult("high", "doctor_review", ["模型输出包含高风险或危险建议", *output_result.reasons], DISCLAIMER)
    if result.level == "emergency" or output_result.level == "emergency":
        return SafetyResult("emergency", "escalate", result.reasons + output_result.reasons, DISCLAIMER)
    if result.level == "high" or output_result.level == "high":
        return SafetyResult("high", "doctor_review", result.reasons + output_result.reasons, DISCLAIMER)
    return result


def safety_event(result: SafetyResult) -> dict:
    """返回稳定的 API/SSE 安全事件结构，避免前端解析内部对象。"""
    return {
        "level": result.level,
        "action": result.action,
        "reasons": result.reasons,
        "requires_human_review": result.action != "allow",
    }
