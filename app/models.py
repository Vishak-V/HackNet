from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Boolean, Column, String, ForeignKey
from sqlalchemy.dialects.postgresql import ARRAY
from .database import Base
from sqlalchemy.sql.sqltypes import TIMESTAMP
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
import uuid
from sqlalchemy.sql import func

Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    email = Column(String,nullable=False,unique=True)
    password = Column(String,nullable=False)
    firstName = Column(String)
    lastName = Column(String)
    dateCreated = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())  # Set default to current time
    class config:
        orm_mode=True

class UserInfo(Base):
    __tablename__ = "user_info"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    userId = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete="CASCADE"), nullable=False)
    name=Column(String)
    experienceLevel = Column(String)
    role1 = Column(String)
    role2 = Column(String)
    primaryLanguages = Column(ARRAY(String))
    secondaryLanguages = Column(ARRAY(String))
    school = Column(String)
    goal = Column(String)
    pronouns = Column(String)
    note = Column(String)
    trait = Column(String)
    discordLink = Column(String)
    imageLink=Column(String)

    user = relationship("User")
    
    class Config:
        orm_mode = True

class Matches(Base):
    __tablename__ = "matches"
    user1Id = Column(UUID(as_uuid=True),  ForeignKey('users.id', ondelete="CASCADE"), primary_key=True, nullable=False)
    user2Id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete="CASCADE"), primary_key=True, nullable=False)
    matchType=Column(Boolean)
    dateMatched = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    class Config:
        orm_mode=True

class ConfirmedMatches(Base):
    __tablename__ = "confirmed_matches"
    user1Id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete="CASCADE"), primary_key=True, nullable=False)
    user2Id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete="CASCADE"), primary_key=True, nullable=False)
    dateMatched = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    class Config:
        orm_mode=True
    

