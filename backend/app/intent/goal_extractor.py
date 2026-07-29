class GoalExtractor:
    """Post-processes and validates extracted actionable goals."""

    def extract(self, raw_goal: str) -> str:
        """
        Cleans and normalizes the goal string to ensure it is brief and actionable.
        """
        cleaned = raw_goal.strip().rstrip(".").rstrip("!")
        if not cleaned:
            return "Process user query"
        # Capitalize first character
        return cleaned[0].upper() + cleaned[1:] if len(cleaned) > 1 else cleaned.upper()
