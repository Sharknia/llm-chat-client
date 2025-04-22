from uuid import UUID

from pydantic import BaseModel, EmailStr

from app.src.domain.user.enums import AuthLevel


# 회원가입 요청 스키마
class UserCreateRequest(BaseModel):
    email: EmailStr
    password: str
    nickname: str


# 사용자 정보 응답 스키마
class UserResponse(BaseModel):
    id: UUID
    email: EmailStr
    nickname: str
    is_active: bool
    auth_level: AuthLevel

    class Config:
        from_attributes = True


# 인증된 사용자 정보 스키마
class AuthenticatedUser(BaseModel):
    user_id: UUID
    email: EmailStr
    nickname: str
    auth_level: AuthLevel
