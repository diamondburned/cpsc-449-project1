from pydantic import BaseModel
from models import *


class LoginRequest(BaseModel):
    first_name: str
    last_name: str


class LoginResponse(BaseModel):
    user: User
    token: str
    expiry: int


class EnrollmentPost(BaseModel):
    user: int
    section: int


class AddCourseRequest(BaseModel):
    code: str
    name: str
    department_id: int


class SectionPost(BaseModel):
    course_id: int
    classrooom: str
    capacity: int
    waitlist_capacity: int
    day: str
    begin_time: str
    end_time: str
    freeze: bool
    instructor_id: int


class ListEnrollmentsResponse(BaseModel):
    enrollments: list[Enrollment]
