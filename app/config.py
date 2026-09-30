from pydantic_settings import BaseSettings, SettingsConfigDict
class Settings(BaseSettings):
    app_name:str="PocketSmart AI"
    secret_key:str="development-only-change-me"
    database_url:str="sqlite:///./pocketsmart.db"
    gemini_api_key:str=""
    gemini_model:str="gemini-2.5-flash"
    access_token_minutes:int=10080
    max_upload_mb:int=5
    model_config=SettingsConfigDict(env_file=".env",extra="ignore",case_sensitive=False)
settings=Settings()
