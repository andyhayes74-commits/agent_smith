from enum import IntEnum


class PermissionLevel(IntEnum):
    """Smith permission levels.

    Level 0 is read-only and should be the default for v1.
    """

    READ_ONLY_OBSERVER = 0
    OPERATOR_ASSISTANT = 1
    SAFE_AUTOMATION_AGENT = 2
    PRODUCTION_SUPERVISOR = 3
    DEVELOPMENT_ASSISTANT = 4


class ActionDeniedError(RuntimeError):
    """Raised when a requested action is outside Smith's current authority."""


def require_permission(current_level: int, required_level: PermissionLevel, action: str) -> None:
    if current_level < required_level:
        raise ActionDeniedError(
            f"Action '{action}' requires Smith permission level {int(required_level)}, "
            f"but current level is {current_level}."
        )
