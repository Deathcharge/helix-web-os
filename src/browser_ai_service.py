"""
🧠 Browser AI Service
AI-powered browser assistant that works with user's selected LLM model.

Features:
- Page summarization
- Content Q&A
- Structured data extraction
- Element finding
- Uses BYOK keys for model selection
"""

import logging
import re
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/web-os/browser/ai", tags=["Browser AI"])


# ============================================================================
# MODELS
# ============================================================================


class BrowserAIRequest(BaseModel):
    """Request for browser AI assistance"""

    action: str = Field(..., description="Action type: analyze, summarize, extract, find, ask")
    page_url: str = Field(..., description="Current page URL")
    page_content: str | None = Field(None, description="Page HTML or text content")
    user_query: str | None = Field(None, description="User's question or instruction")
    extraction_schema: dict[str, Any] | None = Field(None, description="Schema for data extraction")
    model_preference: str | None = Field(None, description="Preferred LLM provider (anthropic, openai, etc.)")


class BrowserAction(BaseModel):
    """Action for browser to execute"""

    type: str  # click, type, scroll, highlight, navigate
    selector: str | None = None
    value: str | None = None
    description: str


class BrowserAIResponse(BaseModel):
    """Response from browser AI"""

    success: bool
    result: str
    actions: list[BrowserAction] = []
    extracted_data: dict[str, Any] | None = None
    confidence: float = 0.9


# ============================================================================
# PROMPT TEMPLATES
# ============================================================================


SUMMARIZE_PROMPT = """You are a helpful browser assistant. Summarize this webpage content concisely.

URL: {url}
Content:
{content}

Provide a clear, helpful summary in 2-3 paragraphs. Focus on the main purpose and key information."""


ASK_PROMPT = """You are a helpful browser assistant. Answer the user's question based on this webpage.

URL: {url}
Content:
{content}

User Question: {query}

Provide a direct, helpful answer based only on the webpage content."""


EXTRACT_PROMPT = """You are a data extraction assistant. Extract structured data from this webpage.

URL: {url}
Content:
{content}

Extraction Request: {query}
Schema (if provided): {schema}

Return the extracted data in a clear, structured format. If specific items are requested, list them."""


FIND_PROMPT = """You are a browser assistant helping find elements on a page.

URL: {url}
Content:
{content}

User wants to find: {query}

Describe where the element is located and suggest a CSS selector if possible.
Format: "The element is [location]. Suggested selector: [selector]" """


# ============================================================================
# CONTENT PROCESSING
# ============================================================================


def sanitize_content(html_content: str, max_length: int = 15000) -> str:
    """
    Clean HTML content for LLM processing.
    Removes scripts, styles, and excessive whitespace.
    """
    if not html_content:
        return ""

    # Remove script and style tags
    content = re.sub(r"<script[^>]*>.*?</script>", "", html_content, flags=re.DOTALL | re.IGNORECASE)
    content = re.sub(r"<style[^>]*>.*?</style>", "", content, flags=re.DOTALL | re.IGNORECASE)

    # Remove HTML comments
    content = re.sub(r"<!--.*?-->", "", content, flags=re.DOTALL)

    # Remove HTML tags but keep text
    content = re.sub(r"<[^>]+>", " ", content)

    # Clean up whitespace
    content = re.sub(r"\s+", " ", content)
    content = content.strip()

    # Truncate if too long
    if len(content) > max_length:
        content = content[:max_length] + "... [truncated]"

    return content


def extract_main_content(html_content: str) -> str:
    """Extract main content, prioritizing article/main elements"""
    # Simple heuristic - in production would use readability algorithms
    content = sanitize_content(html_content)
    return content


# ============================================================================
# AUTHENTICATION
# ============================================================================


async def verify_browser_ai_token(authorization: str = Header(None)) -> dict[str, Any]:
    """Verify JWT token and check tier for browser AI access"""
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

        user_id = payload.get("user_id", "unknown")
        tier = payload.get("tier", "free")

        # Check tier access - Browser AI requires Starter+ (consistent with Web OS)
        blocked_tiers = {"free", "hobby"}
        if tier in blocked_tiers:
            raise HTTPException(
                status_code=403,
                detail="Browser AI requires Starter subscription or higher",
            )

        return {"user_id": user_id, "tier": tier}

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Browser AI auth failed: %s", e)
        raise HTTPException(status_code=401, detail="Authentication failed")


# ============================================================================
# AI SERVICE
# ============================================================================


async def get_llm_response(user_id: str, prompt: str, provider: str | None = None) -> str:
    """
    Get LLM response using user's BYOK key or platform fallback.
    """
    try:
        from apps.backend.llm_agent_engine import get_llm_engine

        engine = get_llm_engine()
        if engine:
            result = await engine.generate_agent_response(
                agent_id="browser_assistant",
                user_message=prompt,
                session_id=f"browser_{user_id}",
                context={"source": "browser_ai"},
            )
            # Unpack tuple (response_text, search_sources)
            if isinstance(result, tuple):
                return result[0]
            return result

        # Fallback to UnifiedLLM when engine unavailable
        try:
            from apps.backend.services.unified_llm import unified_llm

            result = await unified_llm.chat_with_metadata(
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful browser AI assistant. Provide concise, actionable responses about web page content.",
                    },
                    {"role": "user", "content": prompt},
                ],
                max_tokens=500,
                temperature=0.3,
            )
            return result.get("content", result.get("response", ""))
        except Exception:
            return "🤖 AI processing requires an active LLM connection. Please configure your API keys in Settings > Bring Your Own Keys."

    except Exception as e:
        logger.error("LLM request failed: %s", e)
        return "AI processing error. Please check your LLM configuration."


def simulate_ai_response(prompt: str) -> str:
    """Fallback response when LLM is unavailable"""
    if "summarize" in prompt.lower():
        return "📄 **Page Summary**\n\nThis webpage contains information that would need AI processing to summarize. Please ensure your LLM API keys are configured in Settings > BYOT."

    if "find" in prompt.lower():
        return "🔍 **Element Search**\n\nTo find specific elements, I need AI processing. Please configure your API keys in Settings."

    return "🤖 AI processing requires an active LLM connection. Please configure your API keys in Settings > Bring Your Own Keys."


# ============================================================================
# ENDPOINTS
# ============================================================================


@router.post("/analyze")
async def analyze_page(
    request: BrowserAIRequest,
    auth: dict[str, Any] = Depends(verify_browser_ai_token),
) -> BrowserAIResponse:
    """
    Analyze page content with AI.
    Supports: summarize, ask, extract, find actions.
    """
    user_id = auth["user_id"]
    logger.info("Browser AI request from user %s: action=%s", user_id, request.action)

    # Sanitize content
    content = sanitize_content(request.page_content or "")

    if not content:
        return BrowserAIResponse(
            success=False,
            result="No page content provided. Please ensure the page has loaded.",
            confidence=0.0,
        )

    # Build prompt based on action
    action = request.action.lower()

    if action == "summarize":
        prompt = SUMMARIZE_PROMPT.format(url=request.page_url, content=content)
    elif action == "ask":
        if not request.user_query:
            return BrowserAIResponse(
                success=False,
                result="Please provide a question about the page.",
                confidence=0.0,
            )
        prompt = ASK_PROMPT.format(url=request.page_url, content=content, query=request.user_query)
    elif action == "extract":
        prompt = EXTRACT_PROMPT.format(
            url=request.page_url,
            content=content,
            query=request.user_query or "Extract key data",
            schema=request.extraction_schema or "auto-detect",
        )
    elif action == "find":
        if not request.user_query:
            return BrowserAIResponse(
                success=False,
                result="Please describe what element to find.",
                confidence=0.0,
            )
        prompt = FIND_PROMPT.format(
            url=request.page_url,
            content=content[:5000],  # Shorter for element finding
            query=request.user_query,
        )
    else:
        return BrowserAIResponse(
            success=False,
            result=f"Unknown action: {action}. Use: summarize, ask, extract, find",
            confidence=0.0,
        )

    # Get AI response
    result = await get_llm_response(user_id, prompt, request.model_preference)

    return BrowserAIResponse(success=True, result=result, confidence=0.85)


@router.get("/providers")
async def get_available_providers(
    auth: dict[str, Any] = Depends(verify_browser_ai_token),
) -> dict[str, Any]:
    """Get available LLM providers for the user"""
    user_id = auth["user_id"]

    try:

        from apps.backend.services.byot_service import SUPPORTED_PROVIDERS, get_user_byot_status

        status = await get_user_byot_status(user_id)

        available = []
        for key_status in status.keys:
            if key_status.is_set:
                available.append(
                    {
                        "provider": key_status.provider,
                        "name": key_status.provider_name,
                        "ready": True,
                    }
                )

        return {
            "providers": available,
            "supported": list(SUPPORTED_PROVIDERS.keys()),
            "byot_enabled": status.enabled,
        }

    except Exception as e:
        logger.warning("Could not get BYOT status: %s", e)
        return {
            "providers": [],
            "supported": ["anthropic", "openai", "perplexity", "xai"],
            "byot_enabled": False,
        }


@router.get("/capabilities")
async def get_capabilities() -> dict[str, Any]:
    """Get browser AI capabilities"""
    return {
        "actions": [
            {
                "id": "summarize",
                "name": "Summarize",
                "icon": "📄",
                "description": "Get a quick summary of the page",
            },
            {
                "id": "ask",
                "name": "Ask Question",
                "icon": "💬",
                "description": "Ask anything about the page content",
            },
            {
                "id": "extract",
                "name": "Extract Data",
                "icon": "📋",
                "description": "Extract structured data from the page",
            },
            {
                "id": "find",
                "name": "Find Element",
                "icon": "🎯",
                "description": "Locate specific elements on the page",
            },
        ],
        "tier_required": "starter",
        "max_content_length": 15000,
    }


__all__ = ["router"]
