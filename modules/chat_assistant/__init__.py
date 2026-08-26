"""
__init__.py for chat_assistant module — AI Marketing Chat Assistant
"""
from .platforms import (
    PLATFORMS, OBJECTIVES,
    get_platform, get_objective,
    get_all_platforms, get_all_objectives,
)
from .generator import generate_content
