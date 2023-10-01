import sqlite3

conn = sqlite3.connect('database.db')
c = conn.cursor()

c.execute('''CREATE TABLE users (
  user_id INTEGER PRIMARY KEY AUTOINCREMENT,
  first_name TEXT NOT NULL,
  last_name TEXT NOT NULL,
  role TEXT NOT NULL)''')

c.execute('''CREATE TABLE departments (
  department_num INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL)''')

c.execute('''CREATE TABLE courses (
  course_num INTEGER PRIMARY KEY AUTOINCREMENT,
  department_num INTEGER NOT NULL,
  name TEXT NOT NULL,
  FOREIGN KEY (department_num) REFERENCES departments(department_num))''')

c.execute('''CREATE TABLE sections (
  course_num INTEGER NOT NULL,
  section_num INTEGER PRIMARY KEY AUTOINCREMENT,
  classroom TEXT NOT NULL,
  enrolled INTEGER NOT NULL,
  capacity INTEGER NOT NULL,
  waitlist_capacity INTEGER NOT NULL,
  day TEXT NOT NULL,
  beg_time TEXT NOT NULL,
  end_time TEXT NOT NULL,
  instructor INTEGER NOT NULL,
  FOREIGN KEY (course_num) REFERENCES courses(course_num),
  FOREIGN KEY (instructor) REFERENCES users(user_id))''')

c.execute('''CREATE TABLE enrollments (
  user_id INTEGER NOT NULL,
  section_num INTEGER NOT NULL,
  status TEXT NOT NULL,
  grade TEXT,
  PRIMARY KEY (user_id, section_num),
  FOREIGN KEY (user_id) REFERENCES users(user_id),
  FOREIGN KEY (section_num) REFERENCES sections(section_num))''')

c.execute('''CREATE TABLE waitlist (
  user_id INTEGER NOT NULL,
  section_num INTEGER NOT NULL,
  position INTEGER NOT NULL,
  date TEXT NOT NULL,
  PRIMARY KEY (user_id, section_num),
  FOREIGN KEY (user_id) REFERENCES users(user_id),
  FOREIGN KEY (section_num) REFERENCES sections(section_num))''')

conn.commit()
conn.close()