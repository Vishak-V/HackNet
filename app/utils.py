from passlib.context import CryptContext
from app import schemas

import google.generativeai as genai

import PyPDF2 as pdf
from dotenv import load_dotenv
import json
from .config import settings

load_dotenv() ## load all our environment variables

genai.configure(api_key=settings.GOOGLE_API_KEY)

def get_gemini_repsonse(input):
    model=genai.GenerativeModel('gemini-pro')
    response=model.generate_content(input)
    return response.text


#Prompt Template

input_prompt="""
Here is a user's resume:

resume:{text}

Extract the following details and output in the following JSON schema:
"experienceLevel": "string",
"role1": "string",
"role2": "string",
"primaryLanguages": [
"string"
],
"secondaryLanguages": [
"string"
],
"school": "string",

Choose role1 and role2 from the following: front-end, back-end, data Science, business
For languages choose 3 strongest languages related to role1 and 3 other languages related to role2
Experience level should be the experience level for attending an hackathon, choose from beginner, intermediate, expert


I want the response in a json format like this:
{
"experienceLevel": "string",
"role1": "string",
"role2": "string",
"primaryLanguages": [
"string"
],
"secondaryLanguages": [
"string"
],
"school": "string",
}
"""

pwd_context=CryptContext(schemes=["bcrypt"],deprecated="auto")

def hash(password: str):
    return pwd_context.hash(password)

def verifyPassword(plainPassword: str,hashedPassword: str):
    return pwd_context.verify(plainPassword,hashedPassword)

def recommendation(userInfo: schemas.UserInfoResponse, users_info):
    # This function should return a list of possible matches based on the user's responses
    # The list should be in the form of a PossibleMatches object
    pass

def parse(pdfFile):
    text=""
    reader=pdf.PdfReader(pdfFile)
    for page in range(len(reader.pages)):
        page=reader.pages[page]
        text+=str(page.extract_text())
    
    response=get_gemini_repsonse(input_prompt)

    return response

    