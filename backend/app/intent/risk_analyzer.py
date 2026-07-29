import re
from typing import List
from app.intent.enums import RiskLevel
from app.intent.schemas import RiskAssessment


class RiskAnalyzer:
    """Performs risk assessment on user queries to prevent accidental destructive actions."""

    _DESTRUCTIVE_PATTERNS = [
        r"\b(rm\s+-rf|drop\s+table|delete\s+all|wipe\s+database|destroy|format\s+drive)\b",
        r"\bdelete\s+file\b",
    ]

    def assess(self, message: str) -> RiskAssessment:
        """
        Scan query for hazardous patterns and return risk details.
        """
        msg = message.lower()
        reasons: List[str] = []
        level = RiskLevel.SAFE
        requires_confirmation = False

        for pattern in self._DESTRUCTIVE_PATTERNS:
            if re.search(pattern, msg):
                level = RiskLevel.DESTRUCTIVE
                reasons.append(
                    f"Potentially destructive system command pattern detected: '{pattern}'"
                )
                requires_confirmation = True
                break

        if not reasons:
            # Check for high-impact actions (e.g. git commit, git push, deployment)
            if any(
                kw in msg for kw in ["deploy", "push", "commit", "shutdown", "reboot"]
            ):
                level = RiskLevel.HIGH_IMPACT
                reasons.append(
                    "High impact workspace state modification command detected"
                )
                requires_confirmation = True

        return RiskAssessment(
            level=level,
            reasons=reasons or ["Operation is read-only and safe"],
            requires_confirmation=requires_confirmation,
        )
