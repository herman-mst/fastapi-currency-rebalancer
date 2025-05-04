from datetime import datetime, timedelta
from decouple import config

from passlib.context import CryptContext
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.db import get_db
from app import crud
from app.schemas import TokenData

# === Пароли ===
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """
    Hashes a plaintext password using a secure hashing algorithm.

    Args:
        password (str): The plaintext password to be hashed.

    Returns:
        str: The hashed password as a string.
    """
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    """
    Verify that a plain text password matches its hashed counterpart.

    Args:
        plain (str): The plain text password to verify.
        hashed (str): The hashed password to compare against.

    Returns:
        bool: True if the plain text password matches the hashed password, False otherwise.
    """
    return pwd_context.verify(plain, hashed)


# === JWT ===
SECRET_KEY = config("JWT_SECRET_KEY", default="CHANGE_ME")
ALGORITHM = config("JWT_ALGORITHM", default="HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(config("ACCESS_TOKEN_EXPIRE_MINUTES", default=60))

bearer_scheme = HTTPBearer(description="Enter your JWT token")

def create_access_token(data: dict) -> str:
    """
    Generates a JSON Web Token (JWT) for the given data.

    Args:
        data (dict): The payload data to include in the token.

    Returns:
        str: The encoded JWT as a string.

    The token includes an expiration time (`exp`) calculated based on the 
    current UTC time and the `ACCESS_TOKEN_EXPIRE_MINUTES` constant. The 
    token is signed using the `SECRET_KEY` and the specified `ALGORITHM`.
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db)
):
    """
    Retrieve the current user based on the provided JWT token.
    Args:
        credentials (HTTPAuthorizationCredentials): The bearer token extracted from the request's Authorization header.
        db (Session): The database session dependency.
    Returns:
        User: The user object retrieved from the database.
    Raises:
        HTTPException: If the token is invalid, expired, or the user does not exist.
    """
    token = credentials.credentials
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
        token_data = TokenData(user_id=user_id)
    except JWTError:
        raise credentials_exception

    user = crud.get_user(db, token_data.user_id)
    if user is None:
        raise credentials_exception
    return user
