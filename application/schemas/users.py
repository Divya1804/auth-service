import random
from pydantic import BaseModel, EmailStr, ConfigDict, Field, field_validator

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


class ForgotPasswordRequest(BaseModel):
    email_id: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not any(char.isupper() for char in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(char.islower() for char in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(char.isdigit() for char in v):
            raise ValueError("Password must contain at least one number")
        if not any(char in "!@#$%^&*()_+-=[]{}|;:'\",.<>?/`~" for char in v):
            raise ValueError("Password must contain at least one special character")
        return v
