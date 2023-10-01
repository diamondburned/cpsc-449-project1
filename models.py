from pydantic import BaseModel

class User(BaseModel):
    user_id: int
    first_name: str
    last_name: str
    role: str

class Department(BaseModel):
    department_num: int
    name: str

class Course(BaseModel):
    course_num: int
    department_num: int
    name: str

class Section(BaseModel):
    course_num: int
    section_num: int
    classroom: str
    enrolled: int
    capacity: int
    waitlist_capacity: int
    day: str
    beg_time: str
    end_time: str
    instructor: int

class Enrollment(BaseModel):
    user_id: int
    section_num: int
    status: str
    grade: str

class Waitlist(BaseModel):
    user_id: int
    section_num: int
    position: int
    date: str