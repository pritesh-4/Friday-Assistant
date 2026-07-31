import pytest
from app.identity.schemas import IdentityType


def test_registry_prefix_generation(registry):
    id_user = registry.generate_id(IdentityType.USER)
    id_company = registry.generate_id(IdentityType.COMPANY)
    id_tech = registry.generate_id(IdentityType.TECHNOLOGY)

    assert id_user.startswith("user_")
    assert id_company.startswith("company_")
    assert id_tech.startswith("tech_")
    assert len(id_user) > 6


@pytest.mark.asyncio
async def test_register_new_entity(registry, repository):
    entity = await registry.register_entity(
        name="Tony Stark",
        entity_type=IdentityType.PERSON,
        confidence=0.9,
        display_name="Iron Man",
        description="Genius, billionaire, playboy, philanthropist.",
        metadata={"suit": "Mark 85"},
    )

    assert entity.id.startswith("person_")
    assert entity.canonical_name == "Tony Stark"
    assert entity.display_name == "Iron Man"
    assert entity.metadata["suit"] == "Mark 85"

    # Verify primary name alias was registered
    aliases = await repository.get_entity_aliases(entity.id)
    assert "Tony Stark" in aliases
