import re
from typing import List
from app.intent.schemas import Entity


class EntityExtractor:
    """Extracts and validates structured entities from user requests."""

    # Common keywords mapping
    _LANGUAGES = {
        "python",
        "javascript",
        "typescript",
        "html",
        "css",
        "rust",
        "go",
        "c++",
        "c",
        "bash",
    }
    _FRAMEWORKS = {
        "react",
        "nextjs",
        "vue",
        "fastapi",
        "flask",
        "django",
        "express",
        "vite",
        "next.js",
    }
    _CLOUD_PROVIDERS = {"aws", "gcp", "azure", "render", "vercel", "github"}

    def extract_heuristics(self, message: str) -> List[Entity]:
        """
        Extract obvious entities using fast rule-based lookup to supplement semantic results.
        """
        entities = []
        msg = message.lower()

        # Extract programming languages
        for lang in self._LANGUAGES:
            if re.search(r"\b" + re.escape(lang) + r"\b", msg):
                entities.append(Entity(value=lang, category="language", confidence=1.0))

        # Extract frameworks
        for fw in self._FRAMEWORKS:
            if re.search(r"\b" + re.escape(fw) + r"\b", msg):
                entities.append(Entity(value=fw, category="framework", confidence=1.0))

        # Extract cloud/hosting
        for provider in self._CLOUD_PROVIDERS:
            if re.search(r"\b" + re.escape(provider) + r"\b", msg):
                entities.append(
                    Entity(value=provider, category="platform", confidence=1.0)
                )

        return entities
