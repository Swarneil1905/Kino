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

DEMO_ACCOUNTS = [
    {
        "email": "demo-scifi@kino.dev",
        "password": "demopass123",
        "ratings": [(1, 1), (7, 1), (8, 1), (2, 1), (3, -1), (10, 1), (4, 1), (5, 1), (6, -1), (9, 1)],
    },
    {
        "email": "demo-action@kino.dev",
        "password": "demopass123",
        "ratings": [(4, 1), (9, 1), (1, 1), (7, 1), (10, -1), (2, 1), (3, 1), (5, 1), (6, 1), (8, -1)],
    },
    {
        "email": "demo-drama@kino.dev",
        "password": "demopass123",
        "ratings": [(3, 1), (6, 1), (10, 1), (2, 1), (8, 1), (1, -1), (4, -1), (5, 1), (7, 1), (9, -1)],
    },
    {
        "email": "demo-animation@kino.dev",
        "password": "demopass123",
        "ratings": [(5, 1), (2, 1), (8, 1), (1, 1), (7, -1), (3, 1), (6, 1), (4, 1), (9, 1), (10, 1)],
    },
    {
        "email": "demo-mixed@kino.dev",
        "password": "demopass123",
        "ratings": [(1, 1), (2, -1), (3, 1), (4, 1), (5, -1), (6, 1), (7, 1), (8, -1), (9, 1), (10, 1)],
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
