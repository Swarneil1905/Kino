"""Seed five demo accounts with diverse genre ratings for portfolio demos."""

from __future__ import annotations

import asyncio
import uuid

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.db.session import AsyncSessionLocal
from app.models.rating import Rating
from app.models.user import User

# Movie IDs confirmed present in MovieLens dataset (from movie_id_map.json):
# 1=Toy Story, 2=Jumanji, 3=Grumpier Old Men, 5=Father of Bride II,
# 6=Heat, 7=Sabrina, 10=GoldenEye, 11=American President, 16=Casino, 17=Sense & Sensibility
# NOTE: IDs 4, 8, 9 do not exist in our MovieLens subset — do not use them.
DEMO_ACCOUNTS = [
    {
        "email": "demo-scifi@kino.dev",
        "password": "demopass123",
        "ratings": [(1, 1), (7, 1), (16, 1), (2, 1), (3, -1), (10, 1), (6, 1), (5, 1), (17, -1), (11, 1)],
    },
    {
        "email": "demo-action@kino.dev",
        "password": "demopass123",
        "ratings": [(6, 1), (11, 1), (1, 1), (7, 1), (10, -1), (2, 1), (3, 1), (5, 1), (17, 1), (16, -1)],
    },
    {
        "email": "demo-drama@kino.dev",
        "password": "demopass123",
        "ratings": [(3, 1), (17, 1), (10, 1), (2, 1), (16, 1), (1, -1), (6, -1), (5, 1), (7, 1), (11, -1)],
    },
    {
        "email": "demo-animation@kino.dev",
        "password": "demopass123",
        "ratings": [(5, 1), (2, 1), (16, 1), (1, 1), (7, -1), (3, 1), (17, 1), (6, 1), (11, 1), (10, 1)],
    },
    {
        "email": "demo-mixed@kino.dev",
        "password": "demopass123",
        "ratings": [(1, 1), (2, -1), (3, 1), (6, 1), (5, -1), (17, 1), (7, 1), (16, -1), (11, 1), (10, 1)],
    },
]


async def seed_demo_accounts(session: AsyncSession) -> int:
    created = 0
    for account in DEMO_ACCOUNTS:
        user_id = uuid.uuid4()
        stmt = insert(User).values(
            id=user_id,
            email=account["email"],
            password_hash=hash_password(account["password"]),
        ).on_conflict_do_nothing(index_elements=["email"])
        await session.execute(stmt)
        await session.flush()

        result = await session.execute(select(User).where(User.email == account["email"]))
        user = result.scalar_one_or_none()
        if not user:
            continue

        for movie_id, value in account["ratings"]:
            stmt = insert(Rating).values(
                id=uuid.uuid4(),
                user_id=user.id,
                movie_id=movie_id,
                value=value,
            )
            stmt = stmt.on_conflict_do_update(
                index_elements=["user_id", "movie_id"],
                set_={"value": value},
            )
            await session.execute(stmt)
        created += 1

    await session.commit()
    return created


async def main() -> None:
    async with AsyncSessionLocal() as session:
        n = await seed_demo_accounts(session)
        print(f"Seeded {n} demo account(s). Password for all: demopass123")


if __name__ == "__main__":
    asyncio.run(main())
