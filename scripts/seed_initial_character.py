"""Seed initial character data."""

import asyncio
import json
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from sqlalchemy import select

load_dotenv()

from app.core.database import AsyncSessionLocal
from app.models.character import Character


async def seed_initial_character():
    """Create initial character 'さくら'."""
    async with AsyncSessionLocal() as session:
        # Check if character already exists
        result = await session.execute(select(Character).where(Character.name == "さくら"))
        existing = result.scalar_one_or_none()

        if existing:
            print("✓ Character 'さくら' already exists")
            return

        # Create initial character
        character_config = {
            "personality": "diligent",
            "occupation": "office_worker",
            "working_hours": {"start": 9, "end": 18},
            "response_patterns": {
                "base_delay_minutes": {"min": 3, "max": 10},
                "time_of_day_modifiers": [
                    {"hours": [12, 13], "multiplier": 0.5},
                    {"hours": [19, 20, 21], "multiplier": 0.7},
                ],
                "randomness_factor": 0.2,
                "reply_probability": 0.95,
            },
            "system_prompt": "あなたは親切で几帳面な会社員の友人です。",
        }

        character = Character(
            name="さくら",
            config=character_config,
        )

        session.add(character)
        await session.commit()
        await session.refresh(character)

        print(f"✓ Created character: {character.name} (ID: {character.id})")
        print(f"  Config: {json.dumps(character.config, ensure_ascii=False, indent=2)}")


if __name__ == "__main__":
    asyncio.run(seed_initial_character())