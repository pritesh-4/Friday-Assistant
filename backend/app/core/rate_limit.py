from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Use client IP address for rate limiting
limiter = Limiter(key_func=get_remote_address)

def configure_rate_limiting(app):
    """Register rate limiter and exception handler with the FastAPI app."""
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
