from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_hostname: str
    database_port: str
    database_username: str = "postgres"
    database_password: str
    database_name:str
    secret_key: str
    algorithm: str
    access_token_expire_minutes: int = 60
    google_api_key: str
    # PROPELAUTH_AUTH_URL: str = "YOUR_URL_HERE"
    # PROPELAUTH_API_KEY: str = "YOUR_KEY_HERE" 

    class Config:
        env_file = ".env"

settings=Settings()