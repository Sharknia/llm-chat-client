from uuid import UUID

from pydantic import BaseModel, EmailStr

from app.src.domain.user.enums import AuthLevel


# 회원가입 요청 스키마
class UserCreateRequest(BaseModel):
    email: EmailStr
    password: str
    nickname: str


class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str


# 사용자 정보 응답 스키마
class UserResponse(BaseModel):
    id: UUID
    email: EmailStr
    nickname: str
    is_active: bool
    auth_level: AuthLevel

    class Config:
        from_attributes = True


# 로그인 응답 스키마
class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    user_id: UUID


# 인증된 사용자 정보 스키마
class AuthenticatedUser(BaseModel):
    user_id: UUID
    email: EmailStr
    nickname: str
    auth_level: AuthLevel
