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
    capacity INTEGER NOT NULL,
    waitlist_capacity INTEGER NOT NULL,
    day TEXT NOT NULL,
    begin_time TEXT NOT NULL,
    end_time TEXT NOT NULL,
    instructor_id INTEGER NOT NULL REFERENCES users (id),
    freeze BOOLEAN NOT NULL DEFAULT FALSE,
    deleted BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE TABLE enrollments (
    user_id INTEGER NOT NULL REFERENCES users (id),
    section_id INTEGER NOT NULL REFERENCES sections (id),
    status TEXT NOT NULL,
    grade TEXT,
    date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, section_id)
);

CREATE TABLE waitlist (
    user_id INTEGER NOT NULL REFERENCES users (id),
    section_id INTEGER NOT NULL REFERENCES sections (id),
    position INTEGER NOT NULL,
    date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
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
(1, 1, 'CS102', 30, 15, 'Tuesday', '7pm', '9:45pm', 2, 0, 0),
(2, 1, 'CS104', 30, 15, 'Wednesday', '4pm', '6:45pm', 2, 0, 0),
(3, 2, 'MH302', 35, 15, 'Monday', '12pm', '2:45pm', 4, 0, 0),
(4, 2, 'MH107', 32, 15, 'Thursday', '9am', '11:30am', 4, 0, 0);

INSERT INTO enrollments VALUES
(5, 1, 'Enrolled', 'A', '2023-09-15'),
(6, 1, 'Enrolled', 'B', '2023-09-15'),
(7, 1, 'Enrolled', 'C', '2023-09-15'),
(8, 1, 'Enrolled', 'B+', '2023-09-15'),
(9, 2, 'Enrolled', 'A-', '2023-09-15'),
(10, 2, 'Dropped', NULL, '2023-09-15'),
(11, 2, 'Enrolled', 'A+', '2023-09-15'),
(12, 3, 'Enrolled', 'C+', '2023-09-15'),
(13, 3, 'Dropped', NULL, '2023-09-15'),
(14, 4, 'Enrolled', 'A-', '2023-09-15'),
(5, 3, 'Enrolled', 'B', '2023-09-15'),
(6, 4, 'Enrolled', 'B', '2023-09-15'),
(7, 2, 'Enrolled', 'B', '2023-09-15');

-- For waitlist table
INSERT INTO waitlist VALUES
(8, 3, 1, '2023-09-15'),
(9, 2, 1, '2023-09-15'),
(10, 4, 2, '2023-09-15'),
(11, 1, 2, '2023-09-15'),
(12, 3, 3, '2023-09-15'),
(13, 1, 3, '2023-09-15'),
(14, 2, 4, '2023-09-15');
