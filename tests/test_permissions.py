import pytest

from smith.config import Settings
from smith.policies.permissions import ActionDeniedError, PermissionLevel, require_permission


def test_default_permission_level_is_zero() -> None:
    assert Settings(_env_file=None).smith_permission_level == 0


def test_level_zero_is_read_only() -> None:
    assert Settings(smith_permission_level=0, _env_file=None).is_read_only is True


def test_action_requiring_higher_level_fails() -> None:
    with pytest.raises(ActionDeniedError):
        require_permission(0, PermissionLevel.OPERATOR_ASSISTANT, "inspect_operator_queue")


def test_action_at_or_below_current_level_passes() -> None:
    require_permission(1, PermissionLevel.READ_ONLY_OBSERVER, "read_status")
    require_permission(1, PermissionLevel.OPERATOR_ASSISTANT, "draft_operator_reply")
