from enum import Enum
from pydantic import BaseModel


class Role(str, Enum):
    STUDENT = "Student"
    REGISTRAR = "Registrar"
    INSTRUCTOR = "Instructor"


class User(BaseModel):
    id: int
    first_name: str
    last_name: str
    role: Role


class Department(BaseModel):
    id: int
    name: str


class Course(BaseModel):
    id: int
    code: str
    name: str
    department: Department


class Section(BaseModel):
    id: int
    course: Course
    classroom: str | None
    capacity: int
    waitlist_capacity: int
    day: str
    begin_time: str
    end_time: str
    freeze: bool
    instructor: User


class EnrollmentStatus(str, Enum):
    ENROLLED = "Enrolled"
    WAITLISTED = "Waitlisted"
    DROPPED = "Dropped"


class Enrollment(BaseModel):
    user: User
    section: Section
    status: EnrollmentStatus
    grade: str | None


class Waitlist(BaseModel):
    user: User
    section: Section
    position: int
