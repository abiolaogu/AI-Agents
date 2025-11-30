import jwt
import datetime
import os
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from .database import get_db, User, hash_password, check_password
from sqlalchemy.ext.asyncio import AsyncSession

SECRET_KEY = os.getenv("SECRET_KEY", "your-super-secret-key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440 # 24 hours

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

async def register_user(username, password, db: AsyncSession):
    """Registers a new user."""
    try:
        # Check if user exists
        result = await db.execute(select(User).where(User.username == username))
        if result.scalars().first():
            return False
        
        new_user = User(username=username, password_hash=hash_password(password))
        db.add(new_user)
        await db.commit()
        return True
    except Exception:
        return False

async def authenticate_user(username, password, db: AsyncSession):
    """Authenticates a user and returns a JWT if successful."""
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalars().first()

    if user and check_password(user.password_hash, password):
        expiration = datetime.datetime.utcnow() + datetime.timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        token = jwt.encode({
            'user_id': user.id,
            'exp': expiration
        }, SECRET_KEY, algorithm=ALGORITHM)
        return token
    return None

async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)):
    """Dependency to get the current authenticated user."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("user_id")
        if user_id is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception
    
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()
    if user is None:
        raise credentials_exception
    return user
