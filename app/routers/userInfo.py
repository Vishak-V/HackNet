from io import BytesIO
import json
from uuid import UUID
from fastapi import Depends,Response,HTTPException,status,APIRouter,File,UploadFile
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app import oauth2
from ..database import engine,SessionLocal,get_db
from .. import models,schemas,utils
from fastapi.encoders import jsonable_encoder
from fastapi import UploadFile, File,APIRouter,Depends,status,HTTPException
from typing import List
from ..utils import parse
from ..supabase import upload_file_to_supabase

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

@router.post("/uploadfile",status_code=status.HTTP_201_CREATED,response_model=schemas.UserInfoResponse)
async def upload_file(file: UploadFile,db: Session=Depends(get_db),currentUser: schemas.UserResponse = Depends(oauth2.get_current_user)):
    if file.content_type != 'application/pdf':
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid file type")

    #Optionally, save the file to a specific location
    # with open(f"/path/to/save/{file.filename}", "wb") as buffer:
    #     buffer.write(file.file.read())
    # parsed=parse(file.file)
    # return parsed
    file_content = await file.read()

    file_like_object = BytesIO(file_content)
    # Pass the file content to the async parse function
    parsed_data = await parse(file_like_object)
    #json_data = json.loads(parsed_data)
    print(parsed_data)
    parsed_data = json.loads(parsed_data)
    #json_data = json.loads(parsed_data)
    newUserInfo = models.UserInfo(userId=currentUser.id,name=currentUser.firstName+" "+currentUser.lastName, **parsed_data)  # Use .dict() instead of .model_dump()
    db.add(newUserInfo)
    db.commit()
    db.refresh(newUserInfo)
    return newUserInfo

@router.post("/uploadphoto",status_code=status.HTTP_201_CREATED)
async def upload_photo(file: UploadFile,db: Session=Depends(get_db),currentUser: schemas.UserResponse = Depends(oauth2.get_current_user)):
    file_content = await file.read()
    file_name = file.filename
    file_url = upload_file_to_supabase(file_content, file_name)
    if file_url is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Error uploading file")

    updateQuery=db.query(models.UserInfo).filter(models.UserInfo.userId==currentUser.id)
    if not updateQuery.first():
        raise HTTPException(status_code=404, detail="No info found for this user")
    if updateQuery.first().userId!=currentUser.id:
        raise HTTPException(status_code=403, detail="You are not authorized to update this user's info")
    updatedData={"imageLink":file_url}
    updateQuery.update(updatedData)
    db.commit()
    return JSONResponse(content={"message":"Uploaded photo successfully"})

@router.get("/",response_model=schemas.UserInfoResponse)
def get_user_info(db: Session=Depends(get_db),currentUser: schemas.UserResponse = Depends(oauth2.get_current_user)):
    user_info=db.query(models.UserInfo).filter(models.UserInfo.userId==currentUser.id).first()
    if not user_info:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User info not found")
    return jsonable_encoder(user_info)

@router.put("/goal",response_model=schemas.UserInfoResponse)
def update_user_goal(info: schemas.UpdateGoal, db: Session = Depends(get_db), currentUser: schemas.UserResponse = Depends(oauth2.get_current_user)):
    # Find the user record by ID
    updateQuery=db.query(models.UserInfo).filter(models.UserInfo.userId==currentUser.id)
    if not updateQuery.first():
        raise HTTPException(status_code=404, detail="No info found for this user")
    if updateQuery.first().userId!=currentUser.id:
        raise HTTPException(status_code=403, detail="You are not authorized to update this user's info")
    updatedData={"goal":info.goal}
    updateQuery.update(updatedData)
    db.commit()
    return JSONResponse(content={"message":"Goal updated successfully"})

@router.put("/imagelink",response_model=schemas.UserInfoResponse)
def update_user_image(info: schemas.UpdateImageLink, db: Session = Depends(get_db), currentUser: schemas.UserResponse = Depends(oauth2.get_current_user)):
    # Find the user record by ID
    updateQuery=db.query(models.UserInfo).filter(models.UserInfo.userId==currentUser.id)
    if not updateQuery.first():
        raise HTTPException(status_code=404, detail="No info found for this user")
    if updateQuery.first().userId!=currentUser.id:
        raise HTTPException(status_code=403, detail="You are not authorized to update this user's info")
    updatedData={"imageLink":info.imageLink}
    updateQuery.update(updatedData)
    db.commit()
    return JSONResponse(content={"message":"Image uploaded successfully"})

@router.put("/pronouns",response_model=schemas.UserInfoResponse)
def update_user_goal(info: schemas.UpdatePronouns, db: Session = Depends(get_db), currentUser: schemas.UserResponse = Depends(oauth2.get_current_user)):
    # Find the user record by ID
    updateQuery=db.query(models.UserInfo).filter(models.UserInfo.userId==currentUser.id)
    if not updateQuery.first():
        raise HTTPException(status_code=404, detail="No info found for this user")
    if updateQuery.first().userId!=currentUser.id:
        raise HTTPException(status_code=403, detail="You are not authorized to update this user's info")
    updatedData={"pronouns":info.pronouns}
    updateQuery.update(updatedData)
    db.commit()
    return JSONResponse(content={"message":"Pronouns updated successfully"})
