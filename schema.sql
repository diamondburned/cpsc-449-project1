PRAGMA strict = ON;
PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;

CREATE TABLE users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    role TEXT NOT NULL
);

CREATE TABLE departments (
    department_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL
);

CREATE TABLE courses (
    course_id INTEGER PRIMARY KEY AUTOINCREMENT,
    department_id INTEGER NOT NULL REFERENCES departments(department_id),
    name TEXT NOT NULL
);

CREATE TABLE sections (
    course_id INTEGER NOT NULL REFERENCES courses(course_id),
    section_id INTEGER PRIMARY KEY AUTOINCREMENT,
    classroom TEXT NOT NULL,
    enrolled INTEGER NOT NULL,
    capacity INTEGER NOT NULL,
    waitlist_capacity INTEGER NOT NULL,
    day TEXT NOT NULL,
    begin_time TEXT NOT NULL,
    end_time TEXT NOT NULL,
    instructor_id INTEGER NOT NULL REFERENCES users(user_id)
);

CREATE TABLE enrollments (
    user_id INTEGER NOT NULL REFERENCES users(user_id),
    section_id INTEGER NOT NULL REFERENCES sections(section_id),
    status TEXT NOT NULL,
    grade TEXT,
    PRIMARY KEY (user_id, section_id)
);

CREATE TABLE waitlist (
    user_id INTEGER NOT NULL REFERENCES users(user_id),
    section_id INTEGER NOT NULL REFERENCES sections(section_id),
    position INTEGER NOT NULL,
    date TEXT NOT NULL,
    PRIMARY KEY (user_id, section_id)
);
