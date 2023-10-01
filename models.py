from pydantic import BaseModel


class User(BaseModel):
    id: int
    first_name: str
    last_name: str
    role: str


class Department(BaseModel):
    id: int
    name: str


class Course(BaseModel):
    id: int
    code: str
    name: str
    department_id: int


class Section(BaseModel):
    id: int
    course_id: int
    classroom: str | None
    enrolled: int
    capacity: int
    waitlist_capacity: int
    day: str
    beg_time: str
    end_time: str
    instructor: int


class Enrollment(BaseModel):
    user_id: int
    section_id: int
    status: str
    grade: str


class Waitlist(BaseModel):
    user_id: int
    section_id: int
    position: int
    date: str
