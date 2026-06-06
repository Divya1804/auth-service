import random
from pydantic import BaseModel, EmailStr, ConfigDict, Field

from application.core.config import settings

# Schema for User creates (Signup), login, response structure.
# Required fields for user create -> first name, last name, email id, phone no, username, password, address, city, state, pincode, img_url (optional).
# Required fields for user Login -> email, password
# Response we want from user while creating a new user -> first name, last name, email id, phone no, username, img_url(Optional), tokens -> access token, token type.


def generate_avatar():
    seeds = settings.AVATAR_SEEDS.split(",")
    return f"https://api.dicebear.com/10.x/notionists/svg?seed={random.choice(seeds)}&backgroundColor=ffffff00&borderRadius=50"


class UserBase(BaseModel):
    first_name: str
    last_name: str
    email_id: EmailStr
    phone_no: str
    username: str
    img_url: str | None = Field(default_factory=generate_avatar)

    model_config = ConfigDict(from_attributes=True)


class UserCreate(UserBase):
    password: str
    address: str
    city: str
    state: str
    pincode: str


class UserUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    phone_no: str | None = None
    address: str | None = None
    city: str | None = None
    state: str | None = None
    pincode: str | None = None
    img_url: str | None = None


class UserLogin(BaseModel):
    email_id: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(UserBase):
    tokens: Token
