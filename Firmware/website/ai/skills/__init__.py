from skills.registry import (
    SKILLS,
    WRITE_SKILLS,
    SkillResult,
    block_skills,
    run_skill,
    tool_definitions,
)

# Importing a skill module registers its skills.
from skills import camera, control, guidelines, telemetry  # noqa: E402,F401

__all__ = [
    "SKILLS",
    "WRITE_SKILLS",
    "SkillResult",
    "block_skills",
    "run_skill",
    "tool_definitions",
]
