from uuid import UUID
from fastapi import Depends,Response,HTTPException,status,APIRouter,File,UploadFile
from sqlalchemy.orm import Session
from app import oauth2
from ..database import engine,SessionLocal,get_db
from .. import models,schemas,utils
from fastapi.encoders import jsonable_encoder
from fastapi import UploadFile, File,APIRouter,Depends,status,HTTPException
from typing import List


router=APIRouter(
    prefix="/userinfo",
    tags=["userinfo"]
)

@router.post("/",status_code=status.HTTP_201_CREATED,response_model=schemas.UserInfoResponse)
def create_user_info(user: schemas.UserInfoAdd,db: Session=Depends(get_db),currentUser: schemas.UserResponse = Depends(oauth2.get_current_user)):
    newUserInfo = models.UserInfo(userId=currentUser.id,name=currentUser.firstName+" "+currentUser.lastName, **user.model_dump())  # Use .dict() instead of .model_dump()
    db.add(newUserInfo)
    db.commit()
    db.refresh(newUserInfo)
    return newUserInfo

@router.post("/uploadfile")
async def upload_file(file: UploadFile):
    if file.content_type != 'application/pdf':
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid file type")
    
    #Optionally, save the file to a specific location
    # with open(f"/path/to/save/{file.filename}", "wb") as buffer:
    #     buffer.write(file.file.read())
    
    return {"filename": file.filename, "content_type": file.content_type}

@router.get("/",response_model=schemas.UserInfoResponse)
def get_user_info(db: Session=Depends(get_db),currentUser: UUID = Depends(oauth2.get_current_user)):
    user_info=db.query(models.UserInfo).filter(models.UserInfo.userId==currentUser).first()
    if not user_info:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User info not found")
    return jsonable_encoder(user_info)