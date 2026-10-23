from skills.registry import SKILLS, SkillResult, run_skill, tool_definitions

# Importing a skill module registers its skills.
from skills import camera, guidelines, telemetry  # noqa: E402,F401

__all__ = ["SKILLS", "SkillResult", "run_skill", "tool_definitions"]
