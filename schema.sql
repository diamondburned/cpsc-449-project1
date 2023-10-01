PRAGMA strict = ON;
PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;

CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    role TEXT NOT NULL
);

CREATE TABLE departments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL
);

CREATE TABLE courses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT NOT NULL,
    name TEXT NOT NULL,
    department_id INTEGER NOT NULL REFERENCES departments (id)
);

CREATE TABLE sections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    course_id INTEGER NOT NULL REFERENCES courses (id),
    classroom TEXT, -- NULL if online
    enrolled INTEGER NOT NULL,
    capacity INTEGER NOT NULL,
    waitlist_capacity INTEGER NOT NULL,
    day TEXT NOT NULL,
    begin_time TEXT NOT NULL,
    end_time TEXT NOT NULL,
    instructor_id INTEGER NOT NULL REFERENCES users (id)
);

CREATE TABLE enrollments (
    user_id INTEGER NOT NULL REFERENCES users (id),
    section_id INTEGER NOT NULL REFERENCES sections (id),
    status TEXT NOT NULL,
    grade TEXT,
    date TEXT NOT NULL,
    PRIMARY KEY (user_id, section_id)
);

CREATE TABLE waitlist (
    user_id INTEGER NOT NULL REFERENCES users (id),
    section_id INTEGER NOT NULL REFERENCES sections (id),
    position INTEGER NOT NULL,
    date TEXT NOT NULL,
    PRIMARY KEY (user_id, section_id)
);

INSERT INTO users VALUES
(1, 'John', 'Doe', 'Student'),
(2, 'Kenytt', 'Avery', 'Instructor'),
(3, 'Jane', 'Doe', 'Registrar'),
(4, 'Bobby', 'Muir', 'Instructor'),
(5, 'Alice', 'Smith', 'Student'),
(6, 'Bob', 'Jones', 'Student'),
(7, 'Carol', 'Williams', 'Student'),
(8, 'Dave', 'Brown', 'Student'),
(9, 'Eve', 'Miller', 'Student'),
(10, 'Frank', 'Davis', 'Student'),
(11, 'Grace', 'Garcia', 'Student'),
(12, 'Henry', 'Rodriguez', 'Student'),
(13, 'Isabel', 'Wilson', 'Student'),
(14, 'Jack', 'Martinez', 'Student');

INSERT INTO departments VALUES
(1, 'Computer Science'),
(2, 'Engineering'),
(3, 'Mathematics');

INSERT INTO courses VALUES
(1, 'CPSC 449', 'Web Back-End Engineering', 1),
(2, 'MATH 150A', 'Calculus I', 3);

INSERT INTO sections VALUES
(1, 1, 'CS102', 0, 30, 15, 'Tuesday', '7pm', '9:45pm', 2),
(2, 1, 'CS104', 0, 30, 15, 'Wednesday', '4pm', '6:45pm', 2),
(3, 2, 'MH302', 0, 35, 15, 'Monday', '12pm', '2:45pm', 4),
(4, 2, 'MH107', 0, 32, 15, 'Thursday', '9am', '11:30am', 4);
