import logging

# Named so docker/uvicorn logs can be grepped for "growhub." without drowning in access noise.
def get_logger(suffix: str = "") -> logging.Logger:
    name = f"growhub.{suffix}" if suffix else "growhub"
    return logging.getLogger(name)
