"""Entity Registry: allocates prefix IDs and registers new canonical nodes."""

from app.core.logging import get_logger
from app.identity.schemas import IdentityEntity, IdentityType
from app.identity.repository import IdentityRepository
from app.identity.validators import IdentityValidator
from app.utils.helpers import generate_uuid, get_utc_now

logger = get_logger("identity.registry")


class IdentityRegistry:
    """Handles permanent ID structures and initial profile creation."""

    # Map all 23 IdentityType enum values to their unique ID prefixes
    PREFIX_MAP = {
        IdentityType.USER: "user",
        IdentityType.PERSON: "person",
        IdentityType.FRIEND: "friend",
        IdentityType.FAMILY: "family",
        IdentityType.COLLEAGUE: "colleague",
        IdentityType.ORGANIZATION: "org",
        IdentityType.COMPANY: "company",
        IdentityType.PROJECT: "project",
        IdentityType.REPOSITORY: "repo",
        IdentityType.TECHNOLOGY: "tech",
        IdentityType.FRAMEWORK: "framework",
        IdentityType.API: "api",
        IdentityType.AI_MODEL: "model",
        IdentityType.APPLICATION: "app",
        IdentityType.BOOK: "book",
        IdentityType.MOVIE: "movie",
        IdentityType.PLACE: "loc",
        IdentityType.DEVICE: "device",
        IdentityType.EVENT: "event",
        IdentityType.TASK: "task",
        IdentityType.GOAL: "goal",
        IdentityType.FILE: "file",
        IdentityType.DOCUMENT: "doc",
    }

    def __init__(self, repository: IdentityRepository) -> None:
        self.repository = repository

    @classmethod
    def generate_id(cls, entity_type: IdentityType) -> str:
        """Create prefix-based unique identity IDs."""
        prefix = cls.PREFIX_MAP.get(entity_type, "entity")
        short_uuid = generate_uuid().split("-")[0]
        return f"{prefix}_{short_uuid}"

    async def register_entity(
        self,
        name: str,
        entity_type: IdentityType,
        confidence: float = 1.0,
        display_name: str | None = None,
        description: str | None = None,
        metadata: dict | None = None,
        source: str = "user_statement",
    ) -> IdentityEntity:
        """Validate, construct, and save a new canonical profile node."""
        cleaned_name = IdentityValidator.validate_name(name)
        val_type = IdentityValidator.validate_type(entity_type)

        # Check existing first to avoid duplicate creation calls
        existing = await self.repository.get_entity_by_name_or_alias(cleaned_name)
        if existing:
            return existing

        entity_id = self.generate_id(val_type)
        now = get_utc_now()
        disp_name = display_name.strip() if display_name else cleaned_name

        entity = IdentityEntity(
            id=entity_id,
            type=val_type,
            display_name=disp_name,
            canonical_name=cleaned_name,
            aliases=[cleaned_name],
            description=description,
            metadata=metadata or {},
            confidence=confidence,
            created_at=now,
            updated_at=now,
            status="active",
            version=1,
            source_history=[f"Registered via {source} at {now.isoformat()}"],
        )

        await self.repository.save_entity(entity)
        # Register the primary name as the first alias for resolving searches
        await self.repository.add_entity_alias(entity_id, cleaned_name)

        logger.info(
            f"Registered new identity: {entity_id} for '{cleaned_name}' ({val_type.value})"
        )
        return entity

    async def register_alias(self, entity_id: str, alias: str) -> None:
        """Thin backward-compatibility alias mapping."""
        await self.repository.add_entity_alias(entity_id, alias)
