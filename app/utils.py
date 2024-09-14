from typing import Annotated, List
from passlib.context import CryptContext
from app import schemas
import typing_extensions as typing
import google.generativeai as genai

from .model import cos_sim
from pydantic import BaseModel, Field, constr
import pydantic
import PyPDF2 as pdf
from dotenv import load_dotenv
import json
from .config import settings

load_dotenv() ## load all our environment variables


    # Instantiates a client

genai.configure(api_key=settings.google_api_key)

Grade = Annotated[
    str, 
    Field(min_length=1, max_length=1, description="A grade must be a single letter between A and F")
]

class UserParsed(typing.TypedDict):
    experienceLevel: str
    role1: str
    role2: str
    primaryLanguages: List[str]
    secondaryLanguages: List[str]
    school: str

class TeamScore(BaseModel):
    depth:  str
    breadth:  str
    diversity: str
    chemistry: str




async def get_gemini_repsonse_parse(input):
    model=genai.GenerativeModel('gemini-1.5-flash')
    response=model.generate_content(input,generation_config=genai.GenerationConfig(
        response_mime_type="application/json", response_schema=UserParsed, max_output_tokens=100,
    ),)
    return response.text

async def get_gemini_repsonse_roster(input):
    model=genai.GenerativeModel('gemini-1.5-flash')
    try:
        # Request content generation from Gemini with the defined configuration
        response = model.generate_content(
            input,
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json", 
                response_schema=TeamScore,  # Ensure TeamScore is a valid Pydantic model
                max_output_tokens=100
            ),
        )
        return response.text  # Ensure this is the correct attribute you need
    except Exception as e:
        # Log and handle errors gracefully
        print(f"Error during Gemini request: {e}")
        return None


#Prompt Template



pwd_context=CryptContext(schemes=["bcrypt"],deprecated="auto")

def hash(password: str):
    return pwd_context.hash(password)

def verifyPassword(plainPassword: str,hashedPassword: str):
    return pwd_context.verify(plainPassword,hashedPassword)

def recommendation(userInfo: schemas.UserInfoResponse, users_info:List[schemas.UserInfoResponse]):
    
    user_dict = userInfo.model_dump()
    
    users_dicts = [user_info.model_dump() for user_info in users_info]
  
        
    # Call the recommendation function (assuming cos_sim.get_recommendations() exists)
    return cos_sim.get_recommendations(user_dict, users_dicts)

    

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
    

    Choose role1 and role2 from the following: front-end, back-end, data science, business
    For languages choose 3 strongest languages as primaryLanguages related to role1 and 3 other languages as secondaryLanguages related to role2
    Experience level should be the experience level for attending an hackathon, choose from beginner, intermediate, expert. Limit your answer to

   """

    response=await get_gemini_repsonse_parse(input_prompt)
    
    return response

async def getScore(roster):
    print(roster)

    text=""
    for teammate in roster:
        text+=teammate.model_dump_json()
    input_prompt="""You are given a list of hackathon participant information, grade the team from A to D return only one letter on breadth of skill, depth of skill, diversity and team chemistry, 
                    Here is the list - """ + text
                    
    response = await get_gemini_repsonse_roster(input_prompt)


    # Return the response or handle it if it's None
    if response:
        print(response)
        return response  # Or parse response if needed (e.g., JSON parsing)
    else:
        print("Failed to get response from Gemini")
        return None
