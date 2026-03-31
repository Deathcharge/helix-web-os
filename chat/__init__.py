"""
Helix Chat Engine - Production-grade real-time WebSocket chat infrastructure

A standalone, modular chat server that can work independently or integrate
with the Helix Collective ecosystem.

Features:
- Real-time WebSocket messaging
- User authentication and management
- Message history and persistence
- Room/channel management
- Scalable async architecture
- Optional Helix integration
"""

from .core.server import ChatServer
from .core.connection_manager import ConnectionManager
from .core.message_handler import MessageHandler

__version__ = "1.0.0"
__all__ = ["ChatServer", "ConnectionManager", "MessageHandler"]
