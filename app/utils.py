from typing import List
from passlib.context import CryptContext
from app import schemas
import typing_extensions as typing
import google.generativeai as genai

    # Set endpoint to EU 
  
import PyPDF2 as pdf
from dotenv import load_dotenv
import json
from .config import settings

load_dotenv() ## load all our environment variables


    # Instantiates a client

genai.configure(api_key=settings.google_api_key)

class UserParsed(typing.TypedDict):
    experienceLevel: str
    role1: str
    role2: str
    primaryLanguages: List[str]
    secondaryLanguages: List[str]
    school: str

async def get_gemini_repsonse(input):
    model=genai.GenerativeModel('gemini-1.5-flash')
    response=model.generate_content(input,generation_config=genai.GenerationConfig(
        response_mime_type="application/json", response_schema=list[UserParsed], max_output_tokens=100,
    ),)
    print(response)
    return response.text


#Prompt Template



pwd_context=CryptContext(schemes=["bcrypt"],deprecated="auto")

def hash(password: str):
    return pwd_context.hash(password)

def verifyPassword(plainPassword: str,hashedPassword: str):
    return pwd_context.verify(plainPassword,hashedPassword)

def recommendation(userInfo: schemas.UserInfoResponse, users_info):
    # This function should return a list of possible matches based on the user's responses
    # The list should be in the form of a PossibleMatches object
    pass

async def parse(pdfFile):
    pdfFile.seek(0)
    text=""
    reader=pdf.PdfReader(pdfFile)
    for page in range(len(reader.pages)):
        page=reader.pages[page]
        text+=str(page.extract_text())
    input_prompt="""
    Here is a user's resume:

    resume:""" + text + """

    Extract the following details and output in the following JSON schema:
    

    Choose role1 and role2 from the following: front-end, back-end, data Science, business
    For languages choose 3 strongest languages as primaryLanguages related to role1 and 3 other languages as secondaryLanguages related to role2
    Experience level should be the experience level for attending an hackathon, choose from beginner, intermediate, expert. Limit your answer to

   """

    response=await get_gemini_repsonse(input_prompt)
    
    return response

    