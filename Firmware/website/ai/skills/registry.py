from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from typing import Any, Callable, Dict, Iterator, List, Optional, Set

from backend_client import BackendError

# Skills that mutate hubs - blocked for guest demo sessions.
WRITE_SKILLS = frozenset[str]({"set_controls"})
_blocked_skills: ContextVar[frozenset] = ContextVar[frozenset]("blocked_skills", default=frozenset[Any]())


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


@contextmanager
def block_skills(names: Set[str]) -> Iterator[None]:
    token = _blocked_skills.set(frozenset[str](names))
    try:
        yield
    finally:
        _blocked_skills.reset(token)


def tool_definitions(exclude: Optional[Set[str]] = None) -> List[dict]:
    blocked = exclude if exclude is not None else set[Any](_blocked_skills.get())
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
        if s.name not in blocked
    ]


def run_skill(name: str, arguments: dict) -> SkillResult:
    if name in _blocked_skills.get():
        return SkillResult({
            "error": "Guest demo is read-only. Create an account to change lights, pump or heater."
        })
    
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
