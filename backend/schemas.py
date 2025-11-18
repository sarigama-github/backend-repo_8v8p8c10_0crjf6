from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List, Literal

# Each model corresponds to a MongoDB collection using its lowercase class name.

class User(BaseModel):
    username: str = Field(..., min_length=2, max_length=50)
    email: str
    provider: Literal["twitter", "facebook", "instagram", "linkedin", "tiktok", "youtube", "custom"]
    access_token: str
    refresh_token: Optional[str] = None
    account_handle: Optional[str] = None
    avatar_url: Optional[HttpUrl] = None

class Post(BaseModel):
    user_id: str
    platforms: List[Literal["twitter", "facebook", "instagram", "linkedin", "tiktok", "youtube"]]
    content: str = Field(..., min_length=1, max_length=4000)
    media_urls: Optional[List[HttpUrl]] = None
    status: Literal["draft", "scheduled", "posted", "failed"] = "draft"
    scheduled_at: Optional[str] = None  # ISO datetime string
    result_ids: Optional[List[str]] = None  # IDs returned by platforms

class AuditLog(BaseModel):
    action: str
    user_id: Optional[str] = None
    details: Optional[dict] = None
