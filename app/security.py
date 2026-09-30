from datetime import datetime,timedelta,timezone
from jose import jwt,JWTError
from passlib.context import CryptContext
from fastapi import Depends,HTTPException,Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.config import settings
from app.database import get_db
from app.models import User
pwd=CryptContext(schemes=["bcrypt"],deprecated="auto")
oauth=OAuth2PasswordBearer(tokenUrl="/api/auth/login",auto_error=False)
def hash_password(p): return pwd.hash(p)
def verify_password(p,h): return pwd.verify(p,h)
def create_token(uid):
    return jwt.encode({"sub":str(uid),"exp":datetime.now(timezone.utc)+timedelta(minutes=settings.access_token_minutes)},settings.secret_key,algorithm="HS256")
def get_current_user(request:Request,token:str|None=Depends(oauth),db:Session=Depends(get_db)):
    token=token or request.cookies.get("pocketsmart_token")
    if not token: raise HTTPException(401,"Sign in required")
    try: uid=int(jwt.decode(token,settings.secret_key,algorithms=["HS256"])["sub"])
    except (JWTError,KeyError,ValueError): raise HTTPException(401,"Invalid or expired token")
    user=db.get(User,uid)
    if not user: raise HTTPException(401,"User no longer exists")
    return user
