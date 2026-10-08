from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional

from backend_client import BackendError


@dataclass
class SkillResult:
    data: Any
    image_data_url: Optional[str] = None


@dataclass
class Skill:
    name: str
    description: str
    parameters: dict
    handler: Callable[..., Any]


SKILLS: Dict[str, Skill] = {}


def skill(name: str, description: str, properties: Optional[dict] = None, required: Optional[List[str]] = None):
    def register(handler: Callable[..., Any]) -> Callable[..., Any]:
        SKILLS[name] = Skill(
            name=name,
            description=description,
            parameters={
                "type": "object",
                "properties": properties or {},
                "required": required or [],
            },
            handler=handler,
        )
        return handler

    return register


def tool_definitions() -> List[dict]:
    return [
        {
            "type": "function",
            "function": {
                "name": s.name,
                "description": s.description,
                "parameters": s.parameters,
            },
        }
        for s in SKILLS.values()
    ]


def run_skill(name: str, arguments: dict) -> SkillResult:
    found = SKILLS.get(name)
    if found is None:
        return SkillResult({"error": f"Unknown skill '{name}'"})

    allowed = set(found.parameters["properties"])
    kwargs = {key: value for key, value in arguments.items() if key in allowed and value is not None}

    try:
        result = found.handler(**kwargs)
    except BackendError as error:
        return SkillResult({"error": error.detail, "status_code": error.status_code})
    except Exception as error:
        return SkillResult({"error": f"{type(error).__name__}: {error}"})

    return result if isinstance(result, SkillResult) else SkillResult(result)
