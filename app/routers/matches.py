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
    prefix="/matches",
    tags=["matches"]
)

@router.get("/",response_model=schemas.PossibleMatches)
def get_possible_matches(db: Session=Depends(get_db),currentUser: UUID = Depends(oauth2.get_current_user)):

    # Get the user's info
    user_info = db.query(models.UserInfo).filter(models.UserInfo.userId == currentUser).first()
    if not user_info:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User info not found")

    q1,q2,q3,q4=utils.recommendation(user_info)

    existingMatches=db.query(models.Matches).filter(models.Matches.user1Id==currentUser).all()
    existingMatches=[match.user2Id for match in existingMatches]

    dataScience=[userInfo for userInfo in q1 if userInfo.userId not in existingMatches]
    backend=[userInfo for userInfo in q2 if userInfo.userId not in existingMatches]
    frontend=[userInfo for userInfo in q3 if userInfo.userId not in existingMatches]
    business=[userInfo for userInfo in q4 if userInfo.userId not in existingMatches]

    return {"data science":dataScience,"back-end":backend,"front-end":frontend,"business":business}


@router.post("/",status_code=status.HTTP_201_CREATED,response_model=schemas.MatchResponse)
def create_match(match: schemas.MatchAdd,db: Session=Depends(get_db),currentUser: schemas.UserResponse = Depends(oauth2.get_current_user)):
    newMatch = models.Matches(user1Id=currentUser.id, **match.model_dump())
    confirmed=False
    if newMatch.user1Id == newMatch.user2Id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot match with yourself")
    if db.query(models.Matches).filter(models.Matches.user1Id == newMatch.user1Id, models.Matches.user2Id == newMatch.user2Id).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Match already exists")
    if db.query(models.Matches).filter(models.Matches.user1Id == newMatch.user2Id, models.Matches.user2Id == newMatch.user1Id).first():
        confirmedMatch = models.ConfirmedMatches(user1Id=newMatch.user1Id,user2Id=newMatch.user2Id)
        db.add(confirmedMatch)
        db.commit()
        db.refresh(confirmedMatch)
        confirmedMatch = models.ConfirmedMatches(user2Id=newMatch.user1Id,user1Id=newMatch.user2Id)
        db.add(confirmedMatch)
        db.commit()
        db.refresh(confirmedMatch)
        confirmed=True

    db.add(newMatch)
    db.commit()
    db.refresh(newMatch)
    data={"user1Id":newMatch.user1Id,"user2Id":newMatch.user2Id,"confirmed":confirmed}
    return data
