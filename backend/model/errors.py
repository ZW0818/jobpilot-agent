"""Extract allowlisted provider error codes without logging request payloads or keys."""
PROVIDER_ERRORS = {
    "AllocationQuota.FreeTierOnly": "免费额度已用尽，且账号限制继续按量调用",
    "InvalidApiKey": "API Key 无效或不匹配当前地域",
    "AccountOverdue": "账号欠费导致服务暂停",
    "AccessDenied": "账号没有模型访问权限",
    "ModelNotFound": "模型名称不存在或当前地域不可用",
}


def provider_error_code(error: Exception) -> str:
    message = str(error)
    return next((code for code in PROVIDER_ERRORS if code in message), "")
