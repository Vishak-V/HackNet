from passlib.context import CryptContext
from app import schemas

pwd_context=CryptContext(schemes=["bcrypt"],deprecated="auto")

def hash(password: str):
    return pwd_context.hash(password)

def verifyPassword(plainPassword: str,hashedPassword: str):
    return pwd_context.verify(plainPassword,hashedPassword)

def recommendation(userInfo: schemas.UserInfoResponse, users_info):
    # This function should return a list of possible matches based on the user's responses
    # The list should be in the form of a PossibleMatches object
    pass