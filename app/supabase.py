import os
from supabase import create_client, Client
from .config import settings

supabase: Client = create_client(settings.supabase_url, settings.supabase_api_key)

def upload_file_to_supabase(file: bytes, file_name: str):
    try:
        supabase.storage.from_(settings.supabase_bucket_name).upload(path=file_name, file=file)
        file_url = supabase.storage.from_(settings.supabase_bucket_name).get_public_url(file_name)
        return file_url
    except Exception as e:
        return None
