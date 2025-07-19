
from fastapi import Depends, HTTPException, status
from jose import JWTError, jwt
from fastapi.security import OAuth2PasswordBearer
from services.database import get_user_by_email, get_db_session

SECRET_KEY = "your-secret-key"  # Must match the one used for token creation
ALGORITHM = "HS256"

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

async def get_current_user_id(
    token: str = Depends(oauth2_scheme),
    db_session = Depends(get_db_session)
) -> int:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = await get_user_by_email(db_session, email)
    if user is None:
        raise credentials_exception

    return user.id
