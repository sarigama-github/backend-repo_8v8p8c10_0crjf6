from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from schemas import User, Post, AuditLog
from database import db, create_document, get_documents  # provided by environment

app = FastAPI(title="Social Manager API", version="0.1.0")

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ConnectAccountRequest(BaseModel):
    username: str
    email: str
    provider: str
    access_token: str
    refresh_token: Optional[str] = None
    account_handle: Optional[str] = None
    avatar_url: Optional[str] = None

class CreatePostRequest(BaseModel):
    user_id: str
    platforms: List[str]
    content: str
    media_urls: Optional[List[str]] = None
    scheduled_at: Optional[str] = None

@app.get("/test")
async def test():
    try:
        # Simple DB check
        await db.command("ping")
        return {"ok": True, "message": "Connected to database"}
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.post("/connect")
async def connect_account(payload: ConnectAccountRequest):
    # Store connected account tokens (mock OAuth for this demo)
    user = User(
        username=payload.username,
        email=payload.email,
        provider=payload.provider,
        access_token=payload.access_token,
        refresh_token=payload.refresh_token,
        account_handle=payload.account_handle,
        avatar_url=payload.avatar_url,
    )
    doc = await create_document("user", user.model_dump())
    await create_document("auditlog", AuditLog(action="connect", user_id=str(doc.inserted_id), details=user.model_dump()).model_dump())
    return {"message": "Account connected", "user_id": str(doc.inserted_id)}

@app.get("/accounts")
async def list_accounts(provider: Optional[str] = None):
    filt = {"provider": provider} if provider else {}
    docs = await get_documents("user", filt, limit=100)
    # Convert ObjectId to string defensively
    for d in docs:
        if "_id" in d:
            d["_id"] = str(d["_id"])
    return {"accounts": docs}

@app.post("/posts")
async def create_post(payload: CreatePostRequest):
    # Save post as scheduled or draft
    post = Post(
        user_id=payload.user_id,
        platforms=payload.platforms,
        content=payload.content,
        media_urls=payload.media_urls,
        status="scheduled" if payload.scheduled_at else "draft",
        scheduled_at=payload.scheduled_at,
    )
    doc = await create_document("post", post.model_dump())
    await create_document("auditlog", AuditLog(action="create_post", user_id=post.user_id, details=post.model_dump()).model_dump())
    return {"message": "Post saved", "post_id": str(doc.inserted_id)}

class PublishRequest(BaseModel):
    post_id: str

@app.post("/publish")
async def publish_post(req: PublishRequest):
    # In a real integration, you would call each platform API with OAuth
    # For this demo, we simulate posting and store result ids
    # Fetch post data
    posts = await get_documents("post", {"_id": {"$oid": req.post_id}}, limit=1)
    if not posts:
        raise HTTPException(status_code=404, detail="Post not found")
    post = posts[0]

    # Simulate success result ids
    result_ids = [f"{p}-{int(datetime.utcnow().timestamp())}" for p in post.get("platforms", [])]

    # Store a simple audit log; in real app update post status in DB
    await create_document(
        "auditlog",
        AuditLog(action="publish", user_id=post.get("user_id"), details={"post_id": req.post_id, "result_ids": result_ids}).model_dump(),
    )
    return {"message": "Published to platforms", "result_ids": result_ids}
