import os
from fastapi import Depends, FastAPI
from . import models
from .database import engine
from passlib.context import CryptContext
from .routers import user,auth, userInfo, matches
from .config import settings
from fastapi.middleware.cors import CORSMiddleware
from propelauth_fastapi import init_auth
from propelauth_py.user import User

# auth = init_auth(settings.PROPELAUTH_AUTH_URL, settings.PROPELAUTH_API_KEY)


pwd_context=CryptContext(schemes=["bcrypt"],deprecated="auto")

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

origins=["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(user.router)
app.include_router(auth.router)
app.include_router(userInfo.router)
app.include_router(matches.router)

@app.get("/")
def read_root():
    return {"Hello": "World"}

