"""
🖥️ Web OS Module
Browser-based operating system backend
- Terminal execution with sandbox security
- File system operations
- Real-time WebSocket communication
- Context-aware AI chat
- AI-powered browser assistant
"""

from .browser_ai_service import router as browser_ai_router
from .file_system import (
    FileInfo,
    FileSystemManager,
    router as file_system_router,
)
from .os_context_chat import router as os_chat_router
from .terminal_executor import (
    CommandResult,
    TerminalExecutor,
    router as terminal_router,
)

__all__ = [
    "CommandResult",
    "FileInfo",
    "FileSystemManager",
    "TerminalExecutor",
    "browser_ai_router",
    "file_system_router",
    "os_chat_router",
    "terminal_router",
]
