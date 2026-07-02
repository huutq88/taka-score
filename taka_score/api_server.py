"""TAKA Score — HTTP API Server for Client integration.

Provides streamable HTTP/SSE endpoint with API key authorization.
"""
from __future__ import annotations

import os
from starlette.responses import JSONResponse
from starlette.middleware.cors import CORSMiddleware

from taka_score.mcp_server import mcp

# Configure MCP server settings for streamable HTTP transport on /mcp
mcp.settings.streamable_http_path = "/mcp"

# Initialize Starlette app with streamable HTTP transport
app = mcp.streamable_http_app()

api_key = os.environ.get("API_KEY")


class MCPAuthMiddleware:
    """Pure ASGI middleware to authenticate MCP endpoint (does NOT buffer response bodies)."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        path = scope.get("path", "")
        method = scope.get("method", "")

        # Healthcheck endpoints
        if path in ("/", "/health"):
            response = JSONResponse({"status": "ok"})
            await response(scope, receive, send)
            return

        # Protect MCP endpoint
        if path.startswith("/mcp"):
            if method == "OPTIONS":
                await self.app(scope, receive, send)
                return

            if api_key:
                headers = dict(scope.get("headers", []))
                auth_header = headers.get(b"authorization", b"").decode()

                from urllib.parse import parse_qs
                qs = parse_qs(scope.get("query_string", b"").decode())
                query_key = (
                    (qs.get("api_key") or [None])[0]
                    or (qs.get("token") or [None])[0]
                    or (qs.get("apiKey") or [None])[0]
                )

                authorized = (
                    auth_header == f"Bearer {api_key}"
                    or query_key == api_key
                )

                if not authorized:
                    response = JSONResponse(
                        {
                            "error": "Unauthorized. Please provide a valid Bearer token in headers or api_key in query params."
                        },
                        status_code=401,
                    )
                    await response(scope, receive, send)
                    return

        await self.app(scope, receive, send)


# Starlette's add_middleware() prepends to the stack: last-added = outermost.
app.add_middleware(MCPAuthMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["mcp-session-id", "Content-Type", "Accept"],
)


# ── Endpoints ──────────────────────────────────────────────

async def manifest_endpoint(request):
    base_url = str(request.base_url).rstrip("/")
    if "localhost" not in base_url and "127.0.0.1" not in base_url:
        base_url = base_url.replace("http://", "https://")

    tools_list = []
    for name, tool in mcp._tool_manager._tools.items():
        tools_list.append({
            "name": name,
            "description": tool.description
        })

    return JSONResponse({
        "identifier": "taka-score",
        "author": "TAKA Score (GoG Studio)",
        "meta": {
            "title": "TAKA Style Evaluator",
            "description": "Vietnamese novel writing style technical evaluator.",
            "tags": ["mcp", "vietnamese", "nlp", "style", "writing"],
            "avatar": "📝"
        },
        "type": "mcp",
        "mcp": {
            "transport": "streamable-http",
            "url": f"{base_url}/mcp"
        },
        "skills": tools_list
    }, headers={
        "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
        "Pragma": "no-cache",
        "Expires": "0"
    })


app.add_route("/manifest.json", manifest_endpoint, methods=["GET"])
