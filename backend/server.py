from fastapi import FastAPI, APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime, timedelta
import jwt
import bcrypt
from pymongo import IndexModel

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# JWT Configuration
JWT_SECRET = "your-super-secret-jwt-key-change-in-production"
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

# Create the main app
app = FastAPI()
api_router = APIRouter(prefix="/api")
security = HTTPBearer()

# Models
class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: str
    username: str
    password_hash: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class UserCreate(BaseModel):
    email: str
    username: str
    password: str

class UserLogin(BaseModel):
    email: str
    password: str

class UserResponse(BaseModel):
    id: str
    email: str
    username: str
    created_at: datetime

class Link(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    url: str
    icon: Optional[str] = "🔗"
    order: int = 0
    clicks: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)

class LinkCreate(BaseModel):
    title: str
    url: str
    icon: Optional[str] = "🔗"

class LinkPage(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    username: str
    title: str
    description: Optional[str] = ""
    theme_color: str = "#3B82F6"
    theme_font: str = "font-sans"
    links: List[Link] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class LinkPageCreate(BaseModel):
    title: str
    description: Optional[str] = ""
    theme_color: str = "#3B82F6"
    theme_font: str = "font-sans"

class LinkPageUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    theme_color: Optional[str] = None
    theme_font: Optional[str] = None

# Utility Functions
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        token = credentials.credentials
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        user_data = await db.users.find_one({"id": user_id})
        if not user_data:
            raise HTTPException(status_code=401, detail="User not found")
        
        return User(**user_data)
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

# Database Initialization
async def init_db():
    # Create indexes
    await db.users.create_index([("email", 1)], unique=True)
    await db.users.create_index([("username", 1)], unique=True)
    await db.linkpages.create_index([("username", 1)], unique=True)
    await db.linkpages.create_index([("user_id", 1)])

# Auth Endpoints
@api_router.post("/signup")
async def signup(user_data: UserCreate):
    # Check if user exists
    existing_user = await db.users.find_one({"$or": [{"email": user_data.email}, {"username": user_data.username}]})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email or username already exists")
    
    # Create user
    hashed_password = hash_password(user_data.password)
    user = User(
        email=user_data.email,
        username=user_data.username,
        password_hash=hashed_password
    )
    
    await db.users.insert_one(user.dict())
    
    # Create access token
    access_token = create_access_token({"sub": user.id})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": UserResponse(**user.dict())
    }

@api_router.post("/login")
async def login(user_data: UserLogin):
    # Find user
    user_doc = await db.users.find_one({"email": user_data.email})
    if not user_doc or not verify_password(user_data.password, user_doc["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    user = User(**user_doc)
    access_token = create_access_token({"sub": user.id})
    
    return {
        "access_token": access_token,
        "token_type": "bearer", 
        "user": UserResponse(**user.dict())
    }

@api_router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    return UserResponse(**current_user.dict())

# LinkPage Endpoints
@api_router.post("/linkpage")
async def create_linkpage(linkpage_data: LinkPageCreate, current_user: User = Depends(get_current_user)):
    # Check if user already has a linkpage
    existing_page = await db.linkpages.find_one({"user_id": current_user.id})
    if existing_page:
        # Update existing page instead of creating new one
        update_data = linkpage_data.dict()
        update_data["updated_at"] = datetime.utcnow()
        
        await db.linkpages.update_one(
            {"user_id": current_user.id},
            {"$set": update_data}
        )
        
        updated_page = await db.linkpages.find_one({"user_id": current_user.id})
        return LinkPage(**updated_page)
    
    linkpage = LinkPage(
        user_id=current_user.id,
        username=current_user.username,
        **linkpage_data.dict()
    )
    
    try:
        await db.linkpages.insert_one(linkpage.dict())
        return linkpage
    except Exception as e:
        # If duplicate key error, return existing page
        if "duplicate key error" in str(e):
            existing_page = await db.linkpages.find_one({"user_id": current_user.id})
            if existing_page:
                return LinkPage(**existing_page)
        raise HTTPException(status_code=500, detail="Error creating link page")

@api_router.get("/linkpage/my")
async def get_my_linkpage(current_user: User = Depends(get_current_user)):
    linkpage_data = await db.linkpages.find_one({"user_id": current_user.id})
    if not linkpage_data:
        raise HTTPException(status_code=404, detail="Link page not found")
    return LinkPage(**linkpage_data)

@api_router.get("/linkpage/{username}")
async def get_public_linkpage(username: str):
    linkpage_data = await db.linkpages.find_one({"username": username})
    if not linkpage_data:
        raise HTTPException(status_code=404, detail="Link page not found")
    return LinkPage(**linkpage_data)

@api_router.put("/linkpage")
async def update_linkpage(linkpage_data: LinkPageUpdate, current_user: User = Depends(get_current_user)):
    update_data = {k: v for k, v in linkpage_data.dict().items() if v is not None}
    update_data["updated_at"] = datetime.utcnow()
    
    result = await db.linkpages.update_one(
        {"user_id": current_user.id},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Link page not found")
    
    updated_page = await db.linkpages.find_one({"user_id": current_user.id})
    return LinkPage(**updated_page)

@api_router.delete("/linkpage")
async def delete_linkpage(current_user: User = Depends(get_current_user)):
    result = await db.linkpages.delete_one({"user_id": current_user.id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Link page not found")
    return {"message": "Link page deleted successfully"}

# Link Management Endpoints
@api_router.post("/linkpage/links")
async def add_link(link_data: LinkCreate, current_user: User = Depends(get_current_user)):
    linkpage = await db.linkpages.find_one({"user_id": current_user.id})
    if not linkpage:
        raise HTTPException(status_code=404, detail="Link page not found")
    
    new_link = Link(**link_data.dict(), order=len(linkpage.get("links", [])))
    
    await db.linkpages.update_one(
        {"user_id": current_user.id},
        {
            "$push": {"links": new_link.dict()},
            "$set": {"updated_at": datetime.utcnow()}
        }
    )
    
    return new_link

@api_router.put("/linkpage/links/{link_id}")
async def update_link(link_id: str, link_data: LinkCreate, current_user: User = Depends(get_current_user)):
    result = await db.linkpages.update_one(
        {"user_id": current_user.id, "links.id": link_id},
        {
            "$set": {
                "links.$.title": link_data.title,
                "links.$.url": link_data.url,
                "links.$.icon": link_data.icon,
                "updated_at": datetime.utcnow()
            }
        }
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Link not found")
    
    return {"message": "Link updated successfully"}

@api_router.delete("/linkpage/links/{link_id}")
async def delete_link(link_id: str, current_user: User = Depends(get_current_user)):
    result = await db.linkpages.update_one(
        {"user_id": current_user.id},
        {
            "$pull": {"links": {"id": link_id}},
            "$set": {"updated_at": datetime.utcnow()}
        }
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Link not found")
    
    return {"message": "Link deleted successfully"}

@api_router.post("/linkpage/links/{link_id}/click")
async def track_click(link_id: str):
    result = await db.linkpages.update_one(
        {"links.id": link_id},
        {"$inc": {"links.$.clicks": 1}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Link not found")
    
    return {"message": "Click tracked"}

# Include router
app.include_router(api_router)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Startup event
@app.on_event("startup")
async def startup_event():
    await init_db()

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)