from agent.execution import fallback_events, record_fallback
from model.errors import provider_error_code


def test_provider_error_diagnostics_never_copy_credentials():
    error = ValueError("AllocationQuota.FreeTierOnly rejected, request key=sk-secret-test-value")
    assert provider_error_code(error) == "AllocationQuota.FreeTierOnly"
    warnings = []
    token = fallback_events.set(warnings)
    try:
        record_fallback("CoachAgent", error)
    finally:
        fallback_events.reset(token)
    assert "AllocationQuota.FreeTierOnly" in warnings[0]
    assert "sk-secret-test-value" not in warnings[0]
