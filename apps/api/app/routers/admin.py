from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db
from app.models.rating import Rating
from app.models.user import User
from app.schemas.user import AdminUserOut

router = APIRouter(prefix="/admin", tags=["admin"])


async def require_admin(user: Annotated[User, Depends(get_current_user)]) -> User:
    if not user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return user


@router.get("/users", response_model=list[AdminUserOut])
async def list_users(
    _: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[AdminUserOut]:
    result = await db.execute(select(User).order_by(User.created_at.desc()))
    users = result.scalars().all()

    out = []
    for u in users:
        count_result = await db.execute(
            select(func.count()).select_from(Rating).where(Rating.user_id == u.id)
        )
        count = count_result.scalar_one()
        out.append(AdminUserOut(
            id=str(u.id),
            email=u.email,
            auth_provider=u.auth_provider,
            is_admin=u.is_admin,
            last_login_at=u.last_login_at,
            created_at=u.created_at,
            rating_count=count,
        ))
    return out
