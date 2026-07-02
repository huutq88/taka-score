"""TAKA Score — Entry point

Run:
    python -m taka_score                 # stdio transport (default)
    python -m taka_score --http          # streamable-http on :8002
    python -m taka_score --http --reload # with hot reload
"""
import os
import sys


def main():
    if "--http" in sys.argv:
        port = int(os.environ.get("PORT", "8002"))
        reload_active = "--reload" in sys.argv
        import uvicorn
        print(
            f"Starting TAKA Score MCP Server on 0.0.0.0:{port} "
            f"(reload={'enabled' if reload_active else 'disabled'})..."
        )
        uvicorn.run(
            "taka_score.api_server:app",
            host="0.0.0.0",
            port=port,
            log_level="info",
            reload=reload_active,
        )
    else:
        from taka_score.mcp_server import mcp
        mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
