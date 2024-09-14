from uuid import UUID
from pydantic import BaseModel,EmailStr
from typing import Optional,List
from datetime import datetime

class UserResponse(BaseModel):
    id: UUID  # The UUID of the user
    email: str
    firstName: Optional[str]
    lastName: Optional[str]

    class Config:
        orm_mode = True


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    firstName: str
    lastName: str
    dateCreated: datetime = datetime.now()
    class config: 
        orm_mode=True



class UserInfoAdd(BaseModel):
    experienceLevel: Optional[str] 
    role1: Optional[str]
    role2: Optional[str]
    school: Optional[str]
    goal: Optional[str]
    note: Optional[str]
    trait: Optional[str] # Assuming traits is a list of strings
    primaryLanguages: Optional[List[str]]
    secondaryLanguages: Optional[List[str]]
    discordLink: Optional[str]
    imageLink: Optional[str]

    class Config:
        orm_mode = True

class UserInfoResponse(BaseModel):
    id: Optional[UUID]
    userId: UUID
    name: str
    experienceLevel: Optional[str] = None
    role1: Optional[str] = None
    role2: Optional[str] = None
    primaryLanguages: Optional[List[str]] = None
    secondaryLanguages: Optional[List[str]] = None
    school: Optional[str] = None
    goal: Optional[str] = None
    note: Optional[str] = None
    trait: Optional[str] = None
    discordLink: Optional[str] = None
    imageLink: Optional[str] = None

    class Config:
        orm_mode = True

class PossibleMatches(BaseModel):
    
    dataScience : List[UserInfoResponse]
    backend: List[UserInfoResponse]
    frontend: List[UserInfoResponse]
    business: List[UserInfoResponse]
    
class MatchAdd(BaseModel):
    user2Id: UUID
    class Config:
        orm_mode=True

class MatchResponse(BaseModel):
    user1Id: UUID
    user2Id: UUID
    confirmed: bool
    class Config:
        orm_mode=True


class UserLogin(BaseModel):
    email: EmailStr
    password: str
    class config:
        orm_mode=True

class Token(BaseModel):
    access_token: str
    token_type: str
    needOnboarding: bool

class TokenData(BaseModel):
    userId: Optional[UUID]=None
    class config:
        orm_mode=True

class UpdateGoal(BaseModel):
    goal: str
    class Config:
        orm_mode=True

class UpdateImageLink(BaseModel):
    imageLink: str
    class Config:
        orm_mode=True

class ConfirmedMatchesInfo(BaseModel):
    confirmedMatchesInfo:List[UserInfoResponse]

    class Config:
        orm_mode=True

class Roster(BaseModel):
    user1: UserInfoResponse
    user2: UserInfoResponse
    user3: UserInfoResponse

    class Config:
        orm_mode=True



    

