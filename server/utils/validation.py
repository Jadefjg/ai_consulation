"""请求参数校验错误中文提示"""

# 字段名中文映射
FIELD_LABELS = {
    "username": "用户名",
    "password": "密码",
    "confirm_password": "确认密码",
    "old_password": "原密码",
    "new_password": "新密码",
    "real_name": "用户昵称",
    "nickname": "昵称",
    "phone": "手机号",
    "email": "邮箱",
    "gender": "性别",
    "age": "年龄",
    "allergy_history": "过敏史",
    "status": "状态",
    "role": "角色",
    "title": "标题",
    "content": "内容",
    "name": "名称",
    "message": "消息内容",
    "chief_complaint": "主诉",
}


def _field_label(field: str) -> str:
    """获取字段中文名称"""
    return FIELD_LABELS.get(field, field)


def translate_validation_error(err: dict) -> str:
    """
    将 Pydantic 校验错误转为中文提示
    :param err: 单条校验错误字典
    :return: 中文错误信息
    """
    loc = err.get("loc") or []
    field_key = ""
    for item in reversed(loc):
        if isinstance(item, str) and item not in ("body", "query", "path"):
            field_key = item
            break
    label = _field_label(field_key) if field_key else "请求参数"

    err_type = err.get("type", "")
    ctx = err.get("ctx") or {}
    msg = str(err.get("msg") or "")

    if err_type == "string_too_short":
        return f"{label}至少{ctx.get('min_length', 0)}个字符"
    if err_type == "string_too_long":
        return f"{label}不能超过{ctx.get('max_length', 0)}个字符"
    if err_type == "missing":
        return f"请填写{label}"
    if err_type == "int_parsing":
        return f"{label}必须为整数"
    if err_type == "greater_than_equal":
        return f"{label}不能小于{ctx.get('ge')}"
    if err_type == "less_than_equal":
        return f"{label}不能大于{ctx.get('le')}"
    if err_type in ("value_error", "assertion_error"):
        if msg.startswith("Value error, "):
            msg = msg[13:]
        # 已含中文则直接返回
        if any("\u4e00" <= c <= "\u9fff" for c in msg):
            return msg
        return f"{label}格式不正确"

    # 兜底：常见英文提示翻译
    if "at least" in msg and "characters" in msg:
        min_len = ctx.get("min_length")
        if min_len:
            return f"{label}至少{min_len}个字符"
    if "at most" in msg and "characters" in msg:
        max_len = ctx.get("max_length")
        if max_len:
            return f"{label}不能超过{max_len}个字符"

    return msg or "请求参数不正确"


def format_validation_errors(errors: list) -> str:
    """
    合并多条校验错误为一条中文提示
    :param errors: Pydantic 错误列表
    :return: 中文错误信息
    """
    if not errors:
        return "请求参数不正确"
    messages = []
    for err in errors:
        text = translate_validation_error(err)
        if text and text not in messages:
            messages.append(text)
    return "；".join(messages)
