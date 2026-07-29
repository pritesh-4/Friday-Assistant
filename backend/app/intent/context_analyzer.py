from typing import List, Optional
from app.intent.enums import ContextSource
from app.intent.schemas import ContextRequirement


class ContextAnalyzer:
    """Analyzes and infers additional required context sources based on the query state."""

    def analyze(
        self, message: str, file_ids: Optional[List[str]] = None
    ) -> List[ContextRequirement]:
        """
        Rules to automatically append context requirements based on request metadata.
        """
        requirements = []
        msg = message.lower()

        # If files are explicitly attached
        if file_ids:
            requirements.append(
                ContextRequirement(
                    source=ContextSource.FILES,
                    reason="Process explicitly attached user files",
                    confidence=1.0,
                )
            )

        # Heuristics for repository context
        if any(
            kw in msg
            for kw in ["code", "repo", "git", "file", "function", "class", "module"]
        ):
            requirements.append(
                ContextRequirement(
                    source=ContextSource.REPOSITORY,
                    reason="Query codebase files or repository index",
                    confidence=0.85,
                )
            )

        return requirements
