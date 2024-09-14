from uuid import UUID
from fastapi import Depends,Response,HTTPException,status,APIRouter,File,UploadFile
from sqlalchemy.orm import Session
from app import oauth2
from ..database import engine,SessionLocal,get_db
from .. import models,schemas,utils
from fastapi.encoders import jsonable_encoder
from fastapi import UploadFile, File,APIRouter,Depends,status,HTTPException
from typing import List
from app import utils

router=APIRouter(
    prefix="/roster",
    tags=["roster"]
)

@router.get("/")
def get_confirmed_matches(db: Session=Depends(get_db),currentUser: schemas.UserResponse = Depends(oauth2.get_current_user)):

    confirmedMatches = db.query(models.ConfirmedMatches).filter(models.ConfirmedMatches.user1Id == currentUser.id).all()
    
    # Extract user IDs from confirmed matches
    confirmedUserIds = [match.user2Id for match in confirmedMatches]
    if  len(confirmedUserIds)==0:
        return []  # Return an empty list if no confirmed matches

    # Fetch user information for the confirmed user IDs
    matchesInfo = db.query(models.UserInfo).filter(models.UserInfo.userId.in_(confirmedUserIds)).all()

    # Convert ORM models to dictionaries and then to Pydantic models
    users_info_dicts = [user.__dict__ for user in matchesInfo]
    users_info_pydantic = [schemas.UserInfoResponse.model_validate(user_dict) for user_dict in users_info_dicts]

    return users_info_pydantic

@router.post("/",response_model=schemas.UserInfoResponse)
def get_team_score(roster:schemas.Roster,db: Session=Depends(get_db),currentUser: schemas.UserResponse = Depends(oauth2.get_current_user)):

    currentUserInfo=db.query(models.UserInfo).filter(models.UserInfo.userId==currentUser.id).first()

    currentUserInfo=schemas.UserInfoResponse.model_validate(currentUserInfo.__dict__)

    currentRoster=[currentUserInfo,roster.user1,roster.user2,roster.user3]

    teamScore=utils.getScore(currentRoster)

    return teamScore



   
