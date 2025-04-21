from pydantic import BaseModel, EmailStr


# Properties to receive via API on creation
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    username: str | None = None


# Properties shared by models stored in DB
class UserBase(BaseModel):
    email: EmailStr | None = None
    is_active: bool = True
    is_verified: bool = False
    username: str | None = None


# Properties to return to client
class User(UserBase):
    id: int

    class Config:
        from_attributes = True  # SQLAlchemy 모델과 매핑하기 위해 필요 (이전의 orm_mode)


# Schema for authenticated user data derived from token
class AuthenticatedUser(BaseModel):
    user_id: int
    email: EmailStr
