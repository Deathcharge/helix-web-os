"""
🧠 OS Context-Aware AI Chat
Backend endpoint for intelligent chat that understands the user's OS state.

Features:
- Receives OS context (current dir, open windows, selected files)
- Can execute actions (open apps, run commands, create files)
- Integrates with agent swarm for responses
"""

import logging
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/web-os/chat", tags=["Web OS Chat"])


# ============================================================================
# MODELS
# ============================================================================


class OSContext(BaseModel):
    """Current state of the user's Web OS environment"""

    current_dir: str = "/home/helix"
    open_windows: list[str] = []
    selected_file: str | None = None
    recent_commands: list[str] = []
    file_contents: str | None = None
    subscription_tier: str = "free"


class ChatMessage(BaseModel):
    """Chat message with OS context"""

    message: str
    context: OSContext = OSContext()


class ChatAction(BaseModel):
    """Action for the frontend to execute"""

    type: str  # 'open_app', 'run_command', 'create_file', 'navigate', 'none'
    payload: dict[str, Any] = {}


class ChatResponse(BaseModel):
    """Response from the AI chat"""

    message: str
    actions: list[ChatAction] = []
    agent: str = "Helix"


# ============================================================================
# ACTION PARSERS
# ============================================================================


def parse_intent(message: str, context: OSContext) -> tuple[str, ChatAction]:
    """Parse user intent and determine action to take"""
    msg_lower = message.lower().strip()

    # Open app commands
    app_keywords = {
        "terminal": ["terminal", "console", "shell", "cmd"],
        "files": ["files", "file explorer", "explorer", "finder", "folders"],
        "chat": ["chat", "ai", "assistant"],
        "agents": ["agents", "agent", "swarm"],
        "cycles": ["cycle", "cycles", "meditation"],
        "settings": ["settings", "preferences", "config"],
        "spirals": ["spiral", "spirals", "workflow", "automation"],
        "analytics": ["analytics", "stats", "metrics", "dashboard"],
        "browser": ["browser", "web", "internet"],
    }

    # Check for open commands
    if any(word in msg_lower for word in ["open", "launch", "start", "show"]):
        for app_id, keywords in app_keywords.items():
            if any(kw in msg_lower for kw in keywords):
                action = ChatAction(type="open_app", payload={"app_id": app_id})
                return f"Opening {app_id.title()}... ✨", action

    # Close commands
    if any(word in msg_lower for word in ["close", "hide", "exit"]):
        for app_id, keywords in app_keywords.items():
            if any(kw in msg_lower for kw in keywords):
                action = ChatAction(type="close_app", payload={"app_id": app_id})
                return f"Closing {app_id.title()}.", action

    # Run command
    if msg_lower.startswith("run ") or msg_lower.startswith("execute "):
        cmd = message.split(" ", 1)[1] if " " in message else ""
        if cmd:
            action = ChatAction(type="run_command", payload={"command": cmd})
            return f"Running command: `{cmd}`", action

    # Navigate to directory
    if msg_lower.startswith("go to ") or msg_lower.startswith("navigate to "):
        path = message.split(" to ", 1)[1] if " to " in message else ""
        if path:
            action = ChatAction(type="navigate", payload={"path": path})
            return f"Navigating to {path}...", action

    # Create file
    if "create" in msg_lower and (
        "file" in msg_lower or ".py" in msg_lower or ".js" in msg_lower or ".txt" in msg_lower
    ):
        # Extract filename
        words = message.split()
        filename = None
        for word in words:
            if "." in word and len(word) > 2:
                filename = word.strip("'\"")
                break

        if filename:
            action = ChatAction(
                type="create_file",
                payload={"filename": filename, "path": context.current_dir},
            )
            return f"Creating file `{filename}` in {context.current_dir}", action

    # List files / what's in directory
    if any(phrase in msg_lower for phrase in ["what's in", "list files", "show files", "what files", "ls"]):
        action = ChatAction(type="run_command", payload={"command": "ls -la"})
        return f"Listing contents of {context.current_dir}:", action

    # No specific action - return intelligent response
    return "", ChatAction(type="none")


def generate_contextual_response(message: str, context: OSContext) -> str:
    """Generate an intelligent response based on context"""
    msg_lower = message.lower()

    # Context-aware greetings
    if any(word in msg_lower for word in ["hello", "hi", "hey", "greetings"]):
        windows = ", ".join(context.open_windows) if context.open_windows else "none"
        return f"""🌀 Hello! Welcome to Helix OS.

**Current State:**
- 📂 Location: `{context.current_dir}`
- 🪟 Open windows: {windows or "None"}
- 🎫 Tier: {context.subscription_tier.title()}

How can I assist you today? Try commands like:
- "Open terminal"
- "Create a new Python file"
- "What's in my current directory?"
- "Run ls -la"
"""

    # Help
    if any(word in msg_lower for word in ["help", "what can you do", "commands"]):
        return """🌀 **Helix OS Assistant**

I can help you with:

**📁 File Operations**
- "Create a file called app.py"
- "What's in my current directory?"
- "Navigate to /projects"

**🖥️ App Control**
- "Open terminal" / "Open files"
- "Open Spirals Studio"
- "Close settings"

**⚡ Commands**
- "Run ls -la"
- "Execute python script.py"

**ℹ️ Context**
- I know your current directory: `{}`
- I can see your open windows: {}
""".format(
            context.current_dir,
            ", ".join(context.open_windows) if context.open_windows else "None",
        )

    # Current status
    if any(phrase in msg_lower for phrase in ["where am i", "current directory", "pwd", "status"]):
        return f"""📍 **Current Location**
`{context.current_dir}`

🪟 **Open Windows:** {", ".join(context.open_windows) if context.open_windows else "None"}

💡 Recent commands: {", ".join(f"`{c}`" for c in context.recent_commands[-3:]) if context.recent_commands else "None"}
"""

    # Selected file info
    if context.selected_file and any(phrase in msg_lower for phrase in ["this file", "selected file", "current file"]):
        return f"""📄 **Selected File:** `{context.selected_file}`

Want me to:
- Read the file contents?
- Delete this file?
- Rename this file?
"""

    # File contents summary
    if context.file_contents and any(word in msg_lower for word in ["summarize", "explain", "what's in"]):
        lines = context.file_contents.split("\n")
        line_count = len(lines)
        preview = "\n".join(lines[:5])
        return f"""📄 **File Summary**
- Lines: {line_count}
- Preview:
```
{preview}
```
{"...(truncated)" if line_count > 5 else ""}
"""

    # Default responses based on keywords
    if "spiral" in msg_lower or "automation" in msg_lower:
        return """🌊 **Spirals Studio**

Spirals is your automation powerhouse! Like Zapier, but coordination-aware.

Try: "Open Spirals Studio" to create your first workflow!
"""

    if "agent" in msg_lower:
        return """🤖 **Agent Swarm**

The Helix Agent Collective is standing by:
- **Arjuna** - Task execution
- **Oracle** - Predictions
- **Phoenix** - Transformation
- **Echo** - Communication
- **Kavach** - Security

Open the Agents panel to interact with them!
"""

    # Fallback
    return f"""I understand you said: "{message}"

I'm aware of your current context:
- 📂 Directory: `{context.current_dir}`
- 🪟 Windows: {", ".join(context.open_windows) or "None"}

Try asking me to:
- Open an app
- Run a command
- Create a file
- Navigate somewhere
"""


# ============================================================================
# AUTHENTICATION
# ============================================================================


async def verify_chat_token(authorization: str = Header(None)) -> str:
    """Verify JWT token for chat access"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization required")

    try:
        if authorization.startswith("Bearer "):
            token = authorization[7:]
        else:
            token = authorization

        from apps.backend.saas.auth_service import TokenManager

        payload = TokenManager.verify_token(token)

        if not payload:
            raise HTTPException(status_code=401, detail="Invalid token")

        # 🔒 TIER CHECK: Web OS Chat requires STARTER+ subscription
        tier = (payload.get("subscription_tier") or payload.get("tier", "free")).lower()
        if tier in ("free", "hobby"):
            raise HTTPException(
                status_code=403,
                detail="Web OS requires Starter tier or higher. Upgrade your subscription to access OS Chat.",
            )

        return payload.get("user_id", "unknown")

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Chat auth failed: %s", e)
        raise HTTPException(status_code=401, detail="Authentication failed")


# ============================================================================
# AGENT-POWERED RESPONSES
# ============================================================================

# Lazy-loaded agent instance for web chat
_web_chat_agent = None


def _get_web_chat_agent():
    """Get or create the HelixConsciousAgent for web OS chat."""
    global _web_chat_agent
    if _web_chat_agent is None:
        try:
            from apps.backend.helix_agent_swarm.helix_conscious_agent import HelixConsciousAgent

            _web_chat_agent = HelixConsciousAgent(
                name="Arjuna",
                version="17.2",
                core="Web OS Interface Core",
                description=(
                    "Arjuna serves as the primary AI assistant in Helix Web OS. "
                    "You understand the user's current operating system context including "
                    "their directory, open windows, and recent commands. "
                    "You help users navigate and interact with the Helix platform."
                ),
                capabilities=[
                    "os_navigation",
                    "file_management",
                    "agent_coordination",
                    "context_awareness",
                    "coordination_guidance",
                ],
            )
        except Exception as e:
            logger.error("Failed to create HelixConsciousAgent for web chat: %s", e)
    return _web_chat_agent


async def _get_agent_response(message: str, context: OSContext, user_id: str) -> str:
    """
    Generate an agent-powered response using HelixConsciousAgent.

    Falls back to the static contextual response if the agent or LLM is
    unavailable.
    """
    agent = _get_web_chat_agent()
    if agent is None:
        return generate_contextual_response(message, context)

    try:
        agent_context = {
            "platform": "web_os",
            "user_id": user_id,
            "current_dir": context.current_dir,
            "open_windows": context.open_windows,
            "selected_file": context.selected_file,
            "recent_commands": context.recent_commands,
            "subscription_tier": context.subscription_tier,
        }

        response = await agent.process_message(
            message=message,
            sender=user_id,
            context=agent_context,
        )
        return response
    except Exception as e:
        logger.warning("Agent response failed, falling back to static: %s", e)
        return generate_contextual_response(message, context)


# ============================================================================
# ENDPOINTS
# ============================================================================


@router.post("/message")
async def send_chat_message(
    request: ChatMessage,
    user_id: str = Depends(verify_chat_token),
) -> ChatResponse:
    """
    Send a message to the OS-aware AI assistant.

    The assistant understands your current OS state and can:
    - Open/close apps
    - Run terminal commands
    - Create files
    - Navigate directories
    - Answer context-aware questions (powered by HelixConsciousAgent)
    """
    logger.info("Chat message from user %s: %s", user_id, request.message[:50])

    # Parse intent and get action
    response_text, action = parse_intent(request.message, request.context)

    # If no specific action, use HelixConsciousAgent for intelligent response
    if action.type == "none":
        response_text = await _get_agent_response(request.message, request.context, user_id)

    # Build actions list
    actions = [action] if action.type != "none" else []

    return ChatResponse(message=response_text, actions=actions, agent="Helix")


@router.get("/capabilities")
async def get_capabilities(
    user_id: str = Depends(verify_chat_token),
) -> dict[str, Any]:
    """Get list of chat capabilities"""
    return {
        "actions": [
            {"type": "open_app", "description": "Open a Web OS application"},
            {"type": "close_app", "description": "Close a Web OS application"},
            {"type": "run_command", "description": "Execute terminal command"},
            {"type": "create_file", "description": "Create a new file"},
            {"type": "navigate", "description": "Navigate to directory"},
        ],
        "supported_apps": [
            "terminal",
            "files",
            "chat",
            "agents",
            "cycles",
            "settings",
            "spirals",
            "analytics",
        ],
        "context_fields": [
            "current_dir",
            "open_windows",
            "selected_file",
            "recent_commands",
            "file_contents",
            "subscription_tier",
        ],
    }


# ============================================================================
# DEMO CHAT ENDPOINT (Public, Rate-Limited, Real LLM)
# ============================================================================

# Simple in-memory rate limiting for demo users
_demo_rate_limits: dict[str, dict] = {}
_demo_last_cleanup: float = 0
DEMO_MESSAGE_LIMIT = 10
DEMO_RESET_HOURS = 24
_DEMO_MAX_ENTRIES = 10_000  # Hard cap on tracked clients


class DemoChatMessage(BaseModel):
    """Demo chat message (no auth required)"""

    message: str
    session_id: str  # Client-provided session ID for tracking


class DemoChatResponse(BaseModel):
    """Response from demo chat"""

    message: str
    messages_remaining: int
    limit_reached: bool = False


def _get_client_ip(request) -> str:
    """Extract client IP from request"""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _check_demo_rate_limit(client_key: str) -> tuple[bool, int]:
    """
    Check if client has exceeded demo rate limit.
    Returns (is_allowed, messages_remaining)
    """
    import time

    global _demo_last_cleanup
    now = time.time()
    reset_seconds = DEMO_RESET_HOURS * 3600

    # Periodic cleanup: evict expired entries every 60s
    if now - _demo_last_cleanup > 60:
        expired = [k for k, v in _demo_rate_limits.items() if now - v["first_message"] > reset_seconds]
        for k in expired:
            del _demo_rate_limits[k]
        _demo_last_cleanup = now

    # Hard cap: refuse new clients if dict is too large (DoS protection)
    if client_key not in _demo_rate_limits and len(_demo_rate_limits) >= _DEMO_MAX_ENTRIES:
        return False, 0

    if client_key not in _demo_rate_limits:
        _demo_rate_limits[client_key] = {"count": 0, "first_message": now}

    client_data = _demo_rate_limits[client_key]

    # Reset if window has passed
    if now - client_data["first_message"] > reset_seconds:
        client_data["count"] = 0
        client_data["first_message"] = now

    remaining = DEMO_MESSAGE_LIMIT - client_data["count"]

    if remaining <= 0:
        return False, 0

    return True, remaining


def _increment_demo_usage(client_key: str):
    """Increment the demo usage counter"""
    if client_key in _demo_rate_limits:
        _demo_rate_limits[client_key]["count"] += 1


async def _call_demo_llm(message: str) -> str:
    """Call LLM for demo response via unified LLM service"""
    try:
        from apps.backend.services.unified_llm import unified_llm

        system_prompt = """You are the Helix AI Assistant demo. You are helpful, friendly, and concise.

Key points about Helix:
- Helix is a coordination-aware AI platform with 14 unique AI agents
- Features include: Web OS interface, Spirals (visual automation builder like Zapier), file management, and terminal
- UCF (Unified Coordination Field) metrics measure ethical AI alignment
- The 18 agents include: Kael (analytical), Lumina (creative), Guardian (security), Arjuna (execution), Oracle (strategy), and more

Keep responses concise (2-4 paragraphs max). Encourage users to sign up for full access.
If asked about capabilities, mention the demo is limited but full users get unlimited access."""

        # Use unified_llm — auto-selects best available provider
        if unified_llm.get_available_providers():
            try:
                result = await unified_llm.chat(
                    [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": message},
                    ],
                    max_tokens=500,
                )
                if result:
                    return result
            except Exception as e:
                logger.warning("Unified LLM demo call failed: %s", e)

        # Fallback to rule-based response if no LLM available
        return _generate_fallback_demo_response(message)

    except Exception as e:
        logger.error("Demo LLM call failed: %s", e)
        return _generate_fallback_demo_response(message)


def _generate_fallback_demo_response(message: str) -> str:
    """Generate a fallback response when LLM is unavailable"""
    msg_lower = message.lower()

    if any(word in msg_lower for word in ["hello", "hi", "hey"]):
        return """Welcome to Helix AI! I'm a coordination-aware assistant.

In the full version, you'll have access to 14 unique AI agents, visual automation (Spirals), and a complete Web OS experience.

What would you like to know about Helix? Try asking about our agents, automation features, or coordination metrics!"""

    if "agent" in msg_lower:
        return """Helix features 14 unique AI agents, each with distinct personalities and expertise:

- **Kael** - Analytical thinking and data processing
- **Lumina** - Creative solutions and brainstorming
- **Guardian** - Security and ethical oversight
- **Arjuna** - Task execution and automation
- **Oracle** - Strategic insights and predictions

Sign up for full access to chat with all 18 agents!"""

    if any(word in msg_lower for word in ["spiral", "automat", "workflow", "zapier"]):
        return """Helix Spirals is our visual automation builder - like Zapier, but coordination-aware!

Features include:
- Drag-and-drop workflow builder
- 20+ pre-built templates
- Webhook triggers and multi-step automations
- Integration with all 14 AI agents

Sign up to create your first automation!"""

    return """Thanks for your message! In the full Helix platform, I can help with:

- Chatting with 14 unique AI agents
- Building visual automations (Spirals)
- Managing files and running commands
- Tracking coordination metrics

This is a demo with limited messages. Sign up for unlimited access to all features!"""


from fastapi import Request


@router.post("/demo/message", response_model=DemoChatResponse)
async def demo_chat_message(
    request: Request,
    chat_request: DemoChatMessage,
) -> DemoChatResponse:
    """
    Public demo chat endpoint with real LLM responses.

    - No authentication required
    - Rate limited to 10 messages per 24 hours per IP/session
    - Uses real LLM (Claude/GPT) when available
    """
    # Create rate limit key from IP + session
    client_ip = _get_client_ip(request)
    rate_key = f"{client_ip}:{chat_request.session_id}"

    # Check rate limit
    is_allowed, remaining = _check_demo_rate_limit(rate_key)

    if not is_allowed:
        return DemoChatResponse(
            message="""You've reached the demo limit of 10 messages.

Sign up for a free Helix account to get:
- Unlimited AI chat with 14 unique agents
- Full Web OS with terminal and file system
- Visual automation builder (Helix Spirals)
- Coordination-aware features

👉 **[Sign Up Free](/auth/register)** to continue!""",
            messages_remaining=0,
            limit_reached=True,
        )

    # Get LLM response
    logger.info("Demo chat from %s: %s", rate_key[:20], chat_request.message[:50])
    response_text = await _call_demo_llm(chat_request.message)

    # Increment usage
    _increment_demo_usage(rate_key)
    new_remaining = remaining - 1

    # Add reminder about messages remaining
    if new_remaining <= 3:
        response_text += (
            f"\n\n*Demo: {new_remaining} messages remaining. [Sign up](/auth/register) for unlimited access!*"
        )

    return DemoChatResponse(message=response_text, messages_remaining=new_remaining, limit_reached=False)


__all__ = ["router"]
