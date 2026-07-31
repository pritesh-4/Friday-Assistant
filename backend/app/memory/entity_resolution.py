"""Entity Resolution: Deduplication, merging, and conflict resolution."""

from app.core.logging import get_logger
from app.memory.schemas import (
    EntityAttribute,
    ExtractedEntity,
    ExplicitCommand,
)
from app.db.database import database
from app.memory.storage import MemoryStorage
from app.schemas.memory import MemoryType
from app.memory.identity import IdentitySystem
from app.utils.helpers import generate_uuid, get_utc_now

logger = get_logger("memory.entity_resolution")


class EntityResolutionSystem:
    """Detects duplicate profiles, resolves key-value conflicts, and processes user corrections."""

    def __init__(self, storage: MemoryStorage, identity_system: IdentitySystem) -> None:
        self.storage = storage
        self.identity_system = identity_system

    async def resolve_extracted_entities(
        self, extracted_entities: list[ExtractedEntity]
    ) -> dict[str, str]:
        """
        Resolve a list of extracted entities to their canonical database IDs.
        Returns a mapping from the extracted name to the canonical entity ID.
        """
        resolved_mapping: dict[str, str] = {}

        for ext_entity in extracted_entities:
            # 1. Resolve canonical identity (looks up name & aliases)
            canonical = await self.identity_system.resolve_or_create_identity(
                name=ext_entity.name,
                entity_type=ext_entity.type,
                confidence=ext_entity.confidence,
            )
            resolved_mapping[ext_entity.name] = canonical.id

            # 2. Add extra aliases extracted
            for alias in ext_entity.aliases:
                await self.identity_system.add_alias(canonical.id, alias)

            # 3. Resolve and save attributes
            for key, val in ext_entity.attributes.items():
                await self.resolve_attribute(
                    canonical.id, key, val, ext_entity.confidence
                )

        return resolved_mapping

    async def resolve_attribute(
        self, entity_id: str, key: str, value: str, confidence: float
    ) -> None:
        """Update attribute values, managing conflicts based on confidence and history."""
        existing_attrs = await self.storage.get_entity_attributes(entity_id)
        match_attr = next((a for a in existing_attrs if a.key == key), None)

        if match_attr:
            if match_attr.value.lower() == value.lower():
                # Value matches, update confidence if the new one is higher
                if confidence > match_attr.confidence:
                    match_attr.confidence = confidence
                    await self.storage.save_entity_attribute(match_attr)
                return

            # Conflict detected!
            # If the new value has higher or equal confidence, we overwrite it.
            # To preserve history, we can store the previous value under a 'previous_{key}' key
            # or record it as a semantic memory.
            if confidence >= match_attr.confidence:
                # Store the old value as a historic attribute
                history_attr = EntityAttribute(
                    id=generate_uuid(),
                    entity_id=entity_id,
                    key=f"previous_{key}",
                    value=match_attr.value,
                    confidence=match_attr.confidence,
                    created_at=match_attr.created_at,
                    updated_at=get_utc_now(),
                )
                await self.storage.save_entity_attribute(history_attr)

                # Overwrite current attribute with new value
                match_attr.value = value
                match_attr.confidence = confidence
                await self.storage.save_entity_attribute(match_attr)
                logger.info(
                    f"Resolved attribute conflict for {entity_id} - Key '{key}': "
                    f"Updated from '{history_attr.value}' to '{value}'"
                )
        else:
            # New attribute
            new_attr = EntityAttribute(
                id=generate_uuid(),
                entity_id=entity_id,
                key=key,
                value=value,
                confidence=confidence,
                created_at=get_utc_now(),
                updated_at=get_utc_now(),
            )
            await self.storage.save_entity_attribute(new_attr)

    async def merge_entities(self, primary_id: str, secondary_id: str) -> None:
        """Merge a duplicate entity (secondary) into a canonical entity (primary)."""
        if primary_id == secondary_id:
            return

        # 1. Fetch profiles
        primary_profile = await self.identity_system.get_entity_profile(primary_id)
        secondary_profile = await self.identity_system.get_entity_profile(secondary_id)
        if not primary_profile or not secondary_profile:
            return

        logger.info(f"Merging entity {secondary_id} into canonical entity {primary_id}")

        # 2. Merge aliases
        primary_aliases_set = {a.lower() for a in primary_profile["aliases"]}
        for alias in secondary_profile["aliases"]:
            if alias.lower() not in primary_aliases_set:
                await self.storage.add_entity_alias(primary_id, alias)

        # Also add secondary's primary name as alias to primary entity
        secondary_name = secondary_profile["entity"].name
        if secondary_name.lower() not in primary_aliases_set:
            await self.storage.add_entity_alias(primary_id, secondary_name)

        # 3. Merge attributes
        primary_attrs = await self.storage.get_entity_attributes(primary_id)
        primary_attrs_map = {a.key: a for a in primary_attrs}

        secondary_attrs = await self.storage.get_entity_attributes(secondary_id)
        for attr in secondary_attrs:
            if attr.key not in primary_attrs_map:
                await database.execute(
                    "UPDATE entity_attributes SET entity_id = ? WHERE id = ?",
                    (primary_id, attr.id),
                )
            else:
                # Resolve conflict between attributes of the same key
                await self.resolve_attribute(
                    primary_id, attr.key, attr.value, attr.confidence
                )

        # 4. Re-route relationship references
        # Set database values directly for relationships referencing secondary_id
        await database.execute(
            "UPDATE relationships SET source_id = ? WHERE source_id = ?",
            (primary_id, secondary_id),
        )
        await database.execute(
            "UPDATE relationships SET target_id = ? WHERE target_id = ?",
            (primary_id, secondary_id),
        )

        # 5. Delete duplicate secondary entity profile
        await self.storage.delete_entity(secondary_id)

    async def handle_user_correction(self, command: ExplicitCommand) -> str:
        """
        Process explicit commands like 'forget', 'update', or 'correct'
        to modify stored entities, attributes, relationships, or memories.
        """
        action = command.action.lower().strip()
        target = command.target_type.lower().strip()

        if action == "forget":
            # Deletion logic
            if target == "memory":
                # Find matching memories via search query
                from app.db.vector_store import vector_store

                # Search across semantic, episodic, procedural, project collections
                deleted_any = False
                for mem_type in ["semantic", "episodic", "procedural", "project"]:
                    collection = f"{mem_type}_memories"
                    docs = await vector_store.search(
                        collection, command.query, n_results=1
                    )
                    if docs:
                        doc = docs[0]
                        # Verify it has close distance or matches closely
                        if doc.get("distance", 1.0) < 0.4:
                            await self.storage.delete_cognitive_memory(
                                doc["id"], MemoryType(mem_type)
                            )
                            deleted_any = True
                if deleted_any:
                    return f"I have forgotten the details matching '{command.query}'."
                return f"I couldn't find any memories matching '{command.query}' to forget."

            elif target in ("entity", "person", "project"):
                entity = await self.storage.get_entity_by_name_or_alias(command.query)
                if entity:
                    await self.storage.delete_entity(entity.id)
                    return f"I have forgotten all records regarding '{entity.name}'."
                return f"I couldn't find any entity profile matching '{command.query}'."

        elif action in ("update", "correct"):
            # Update/correction logic
            if target == "attribute":
                # Expects a detail format like "entity_name:attribute_key" in command.query
                # and command.update_value as the new value.
                parts = command.query.split(":")
                entity_name = parts[0].strip()
                attr_key = parts[1].strip() if len(parts) > 1 else None

                entity = await self.storage.get_entity_by_name_or_alias(entity_name)
                if entity and attr_key:
                    await self.resolve_attribute(
                        entity.id, attr_key, command.update_value or "", 1.0
                    )
                    return f"I have corrected {entity.name}'s {attr_key} to '{command.update_value}'."
                elif entity and not attr_key:
                    # Update primary name
                    entity.name = command.update_value or entity.name
                    await self.storage.save_entity(entity)
                    return f"I have renamed the entity profile to '{command.update_value}'."
                return f"I couldn't locate entity profile '{entity_name}' to update."

            elif target == "memory":
                # Find matching memory in vector store and modify content
                from app.db.vector_store import vector_store

                for mem_type in ["semantic", "episodic", "procedural", "project"]:
                    collection = f"{mem_type}_memories"
                    docs = await vector_store.search(
                        collection, command.query, n_results=1
                    )
                    if docs and docs[0].get("distance", 1.0) < 0.4:
                        mem_id = docs[0]["id"]
                        content = command.update_value or ""
                        # Save updated content to SQL
                        now = get_utc_now().isoformat()
                        if mem_type == "semantic":
                            await database.execute(
                                "UPDATE semantic_memories SET fact = ?, updated_at = ? WHERE id = ?",
                                (content, now, mem_id),
                            )
                        elif mem_type == "episodic":
                            await database.execute(
                                "UPDATE episodic_memories SET details = ?, updated_at = ? WHERE id = ?",
                                (content, now, mem_id),
                            )
                        elif mem_type == "procedural":
                            await database.execute(
                                "UPDATE procedural_memories SET steps = ?, updated_at = ? WHERE id = ?",
                                (content, now, mem_id),
                            )
                        elif mem_type == "project":
                            await database.execute(
                                "UPDATE project_memories SET content = ?, updated_at = ? WHERE id = ?",
                                (content, now, mem_id),
                            )

                        # Update vector db
                        await vector_store.update_memory(
                            collection_name=collection,
                            memory_id=mem_id,
                            text=content,
                            metadata={"type": mem_type},
                        )
                        return f"I have updated the memory matching '{command.query}'."

        return "I received the command but was unable to map the target parameters."
