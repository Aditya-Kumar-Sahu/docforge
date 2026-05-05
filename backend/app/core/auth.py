from typing import cast
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from app.core.config import settings
from app.models.models import User
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from sqlalchemy import select

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    token = credentials.credentials
    
    try:
        # Decode token using Supabase JWT secret
        payload = jwt.decode(
            token, 
            settings.SUPABASE_JWT_SECRET, 
            algorithms=["HS256"],
            audience="authenticated"
        )
        user_id = cast(str | None, payload.get("sub"))
        email = cast(str | None, payload.get("email"))
        
        if user_id is None or email is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
            )
            
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )

    # Check if user exists in our DB, if not, create them (lazy sync)
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        user = User(id=user_id, email=email)
        db.add(user)
        await db.commit()
        await db.refresh(user)
        
    return user
