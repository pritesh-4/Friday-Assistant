from app.intent.exceptions import InvalidRequestException


class IntentGateway:
    """Entry point for checking query boundaries and formatting constraints."""

    def validate_and_preprocess(self, message: str) -> str:
        """
        Verify request length and validity. Strips surrounding whitespace.
        Raises InvalidRequestException if message is empty.
        """
        cleaned = message.strip()
        if not cleaned:
            raise InvalidRequestException("User request message cannot be empty.")
        return cleaned
