from datetime import datetime,timezone
from sqlalchemy import String,Integer,DateTime,ForeignKey,Text
from sqlalchemy.orm import Mapped,mapped_column,relationship
from app.database import Base
def utcnow(): return datetime.now(timezone.utc)
class User(Base):
    __tablename__="users"
    id:Mapped[int]=mapped_column(Integer,primary_key=True)
    name:Mapped[str]=mapped_column(String(100),nullable=False)
    email:Mapped[str]=mapped_column(String(255),unique=True,index=True,nullable=False)
    password_hash:Mapped[str]=mapped_column(String(255),nullable=False)
    created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=utcnow)
    recommendations=relationship("Recommendation",back_populates="user",cascade="all, delete-orphan")
class Recommendation(Base):
    __tablename__="recommendations"
    id:Mapped[int]=mapped_column(Integer,primary_key=True)
    user_id:Mapped[int]=mapped_column(ForeignKey("users.id"),index=True)
    planner:Mapped[str]=mapped_column(String(30),nullable=False)
    title:Mapped[str]=mapped_column(String(200),nullable=False)
    budget:Mapped[int]=mapped_column(Integer,nullable=False)
    input_json:Mapped[str]=mapped_column(Text,nullable=False)
    result_json:Mapped[str]=mapped_column(Text,nullable=False)
    created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=utcnow)
    user=relationship("User",back_populates="recommendations")
