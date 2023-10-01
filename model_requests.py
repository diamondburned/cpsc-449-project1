from pydantic import BaseModel
from models import *


class LoginRequest(BaseModel):
    first_name: str
    last_name: str


class LoginResponse(BaseModel):
    user: User
    token: str
    expiry: int


class ListEnrollmentsResponse(BaseModel):
    enrollments: list[Enrollment]
