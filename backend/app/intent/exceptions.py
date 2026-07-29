class IntentEngineError(Exception):
    """Base exception for all Intent Engine errors."""

    pass


class IntentClassificationError(IntentEngineError):
    """Raised when intent classification fails."""

    pass


class LowConfidenceException(IntentEngineError):
    """Raised when the classification confidence is below the threshold."""

    def __init__(self, message: str, confidence: float, prompt: str):
        super().__init__(message)
        self.confidence = confidence
        self.prompt = prompt


class InvalidRequestException(IntentEngineError):
    """Raised when the input query is malformed or empty."""

    pass
