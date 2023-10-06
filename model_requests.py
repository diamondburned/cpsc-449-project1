from pydantic import BaseModel
from models import *


class LoginRequest(BaseModel):
    first_name: str
    last_name: str


class LoginResponse(BaseModel):
    user: User
    token: str
    expiry: int


class ListUserSectionsType(str, Enum):
    ALL = "all"
    ENROLLED = "enrolled"
    INSTRUCTING = "instructing"


class CreateEnrollmentRequest(BaseModel):
    section: int


class CreateEnrollmentResponse(Enrollment):
    waitlist_position: int | None


class AddCourseRequest(BaseModel):
    code: str
    name: str
    department_id: int


class AddSectionRequest(BaseModel):
    classroom: str
    capacity: int
    waitlist_capacity: int = 15
    day: str
    begin_time: str
    end_time: str
    freeze: bool
    instructor_id: int


class ListEnrollmentsResponse(BaseModel):
    enrollments: list[Enrollment]


class UpdateSectionRequest(BaseModel):
    classroom: str | None
    capacity: int | None
    waitlist_capacity: int | None
    day: str | None
    begin_time: str | None
    end_time: str | None
    freeze: bool | None
    instructor_id: int | None
