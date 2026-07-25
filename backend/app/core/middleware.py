import uuid
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.logging import request_id_ctx, conversation_id_ctx

class RequestContextMiddleware(BaseHTTPMiddleware):
    """
    Middleware to inject Request ID and Conversation ID into ContextVars.
    This allows the structured logger to automatically attach them to every log line.
    """
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate or extract request ID
        req_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.request_id = req_id
        
        # Extract optional conversation ID from headers (if provided by client)
        conv_id = request.headers.get("X-Conversation-ID")
        
        # Set context variables for the current async task
        req_token = request_id_ctx.set(req_id)
        conv_token = conversation_id_ctx.set(conv_id) if conv_id else None
        
        try:
            response = await call_next(request)
            response.headers["X-Request-ID"] = req_id
            return response
        finally:
            request_id_ctx.reset(req_token)
            if conv_token:
                conversation_id_ctx.reset(conv_token)
