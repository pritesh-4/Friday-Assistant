import asyncio
from typing import Any

from duckduckgo_search import DDGS

from app.schemas.execution import PermissionLevel, RetryConfig
from app.tools.base import BaseTool


class WebSearchTool(BaseTool):
    """Tool for searching the web."""

    @property
    def name(self) -> str:
        return "web_search"

    @property
    def description(self) -> str:
        return (
            "Search the web for up-to-date information. "
            "Use this tool when you need to answer questions about current events, "
            "recent developments, or facts that require internet access. "
            "Returns a summary of the top search results."
        )

    @property
    def permission_level(self) -> PermissionLevel:
        return PermissionLevel.SAFE

    @property
    def retry_policy(self) -> RetryConfig:
        return RetryConfig(max_retries=2, backoff_factor=1.5, max_backoff=5.0)

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query to look up on the web.",
                }
            },
            "required": ["query"],
        }

    async def execute(self, query: str, **kwargs) -> str:
        def _search():
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=5))
                return results

        try:
            results = await asyncio.to_thread(_search)
            if not results:
                return f"No web search results found for: '{query}'"

            output = []
            for i, r in enumerate(results):
                title = r.get("title", "No Title")
                href = r.get("href", "No URL")
                body = r.get("body", "No snippet available.")
                output.append(
                    f"Result {i + 1}:\nTitle: {title}\nURL: {href}\nSnippet: {body}\n"
                )

            return "\n".join(output)
        except Exception as e:
            return f"Web search failed: {e!s}"
